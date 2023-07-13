import asyncio
import aiohttp
from pathlib import Path, PurePath
import json
import os
from tqdm import tqdm
from urllib.parse import urlparse
import tenacity
import aiofiles
import argparse

################################## argument parsing ###########################################
parser = argparse.ArgumentParser()
parser.add_argument(
    "--download-dir",
    type=str,
    default="downloads/",
    help="Directory where the images will be downloaded",
)
parser.add_argument(
    "--metadata",
    type=str,
    default="data/metadata/english.metadata",
    help="Metadata file of the article",
)
parser.add_argument(
    "--start-idx", type=int, default=0, help="Starting index of article list slice"
)
parser.add_argument(
    "--end-idx", type=int, default=1000, help="Ending index of article list slice"
)
parser.add_argument(
    "--step", type=int, default=1, help="Step size of articles list slice"
)
parser.add_argument(
    "--max-retry",
    type=int,
    default=5,
    help="Maximum retry count if file download fails",
)
parser.add_argument(
    "--timeout", type=int, default=600, help="Timeout for download request, in seconds"
)
parser.add_argument("--quiet", action="store_true", help="Don't print progressbar")

args = parser.parse_args()

DOWNLOAD_DIR = Path(args.download_dir)
METADATA_FILE = Path(args.metadata)

START_IDX = args.start_idx
END_IDX = args.end_idx
STEP = args.step
MAX_RETRY = args.max_retry
TIMEOUT = args.timeout
QUIET = args.quiet
############################################################################################

# there are 320722 articles
article_slice = slice(START_IDX, END_IDX, STEP)

progress_bar: tqdm


def get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc
    return base_url


def read_metadata_file(path: Path) -> list[dict]:
    """Read metadata file, where each line contains a JSON. These JSONs are converted to pytho dicts,
    and a list of dicts is returned.

    Args:
        path (Path): Path to metadata file. File should contain a JSON in each line.

    Returns:
        list[dict]: List of JSONs in the metadata file, converted to List of Dictionaries.
    """
    with path.open() as f:
        lines = f.readlines()

    return [json.loads(line) for line in lines]


@tenacity.retry(
    reraise=True,
    stop=tenacity.stop_after_attempt(MAX_RETRY),
    wait=tenacity.wait_random(min=3, max=10),
)
async def download_img(session: aiohttp.ClientSession, url: str, filepath: Path):
    """Downloads the file from the provided URL asynchronously.

    Args:
        session (aiohttp.ClientSession): `aiohttp` Client session to connect to URL
        url (str): URL to the downloadable binary
        filepath (Path): Path to save the downloaded content
    """
    async with session.get(url, ssl=False) as response:
        if response.status != 200:
            raise Exception("Response was not 200")

        async with aiofiles.open(str(filepath), "wb") as f:
            await f.write(await response.read())


def is_skip_link(imgurl: str) -> bool:
    """Skip download link if it is not an image format file.

    Args:
        imgurl (str): Image URL

    Returns:
        bool: Should this download link be skipped
    """
    return (
        imgurl.endswith((".html", ".svg"))
        or imgurl.startswith(
            (
                "https://platform.twitter.com",
                "https://www.facebook.com",
                "https://www.youtube.com",
            )
        )
        or any(
            substr in imgurl
            for substr in [
                "iframe.html",
                "?",
            ]
        )
    )


def write_dict_to_json_file(json_file: Path, data_dicts: list[dict]):
    """Write data dict to JSON file.

    Args:
        json_file (Path): JSON file path
        data_dicts (list[dict]): List of dictionaries
    """
    with json_file.open("w") as f:
        json.dump(data_dicts, f, indent=2)


async def download_article_media(article: dict):
    """Download all the media of the provided article. Assign ID to each image, and map to it's article and
    relative position in the article.

    Each downloaded media is stored in a directory named by it's article ID. Each directory consists of the media
    files and metadata files. The images that were successfully downloaded have their metadata in
    `successful_metadata.json`, and the images that failed for some reason have their metadata in
    `exceptions_metadata.json` for each article.

    - Has to be a stateless function for parallelism

    Args:
        article (dict): Dictionary with article metadata
    """
    successful_img_list = []
    exceptions_img_list = []
    skipped_links = []

    article_dir = Path(article["id"])
    article_dir.mkdir(exist_ok=True)

    article_base_url = get_base_url(article["url"])

    # iterate over each media of this article
    async with aiohttp.ClientSession(trust_env=True) as session:
        for idx, img_url in enumerate(article["media_links"]):
            if img_url and img_url[0] == "/":
                # double //
                img_url = img_url[1:] if img_url[1] == "/" else img_url
                img_url = article_base_url + img_url

            # getting image file name
            img_name = PurePath(img_url).name

            # image metadata to be stored
            data = {
                "Id": f"{article['id']}_{idx}",
                "Image Path": str(article_dir / img_name),
                "Article Id": article["id"],
                "Article URL": article["url"],
                "Article Index": idx,
                "Image URL": img_url,
            }

            if is_skip_link(img_url):
                skipped_links.append(data)
                continue

            try:
                _ = await asyncio.wait_for(
                    download_img(session, img_url, article_dir / img_name), TIMEOUT
                )
                successful_img_list.append(data)
            except Exception as e:
                # download failed for some reason
                try:
                    # delete partially downloaded file if any
                    Path(data["Image Path"]).unlink(missing_ok=True)
                except:
                    pass

                data["Exception"] = f"[Exception]: {str(e)}"
                exceptions_img_list.append(data)

    write_dict_to_json_file(
        article_dir / "successful_metadata.json", successful_img_list
    )

    if len(exceptions_img_list) > 0:
        write_dict_to_json_file(
            article_dir / "exceptions_metadata.json", exceptions_img_list
        )

    if len(skipped_links) > 0:
        write_dict_to_json_file(article_dir / "skipped_links.json", skipped_links)

    if not QUIET:
        progress_bar.update()


async def main():
    print(f"Download from {START_IDX} to {END_IDX}...")
    metadata = read_metadata_file(METADATA_FILE)
    total_articles = len(metadata)
    print(f"metadata read, there are {total_articles} articles")

    # downloads will be placed in this directory
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    os.chdir(DOWNLOAD_DIR)

    metadata_slice = metadata[article_slice]

    if not QUIET:
        global progress_bar
        nrows = 8
        pos = ((START_IDX // 500) % nrows) + 1
        progress_bar = tqdm(
            total=len(metadata_slice),
            desc=f"[{START_IDX}, {END_IDX})",
            position=pos,
            leave=False,
            dynamic_ncols=True,
        )

    tasks = []
    for article in metadata_slice:
        task = asyncio.ensure_future(download_article_media(article))
        tasks.append(task)

    await asyncio.gather(*tasks)

    if not QUIET:
        progress_bar.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
