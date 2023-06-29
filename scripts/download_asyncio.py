import asyncio
import aiohttp
from pathlib import Path, PurePath
import json
import os
from tqdm import tqdm
from urllib.parse import urlparse
import tenacity


# there are 320722 articles
article_slice = slice(10000)

DOWNLOAD_CHUNK = 1024

progress_bar: tqdm

EXCEPTION_FILE = Path("exceptions.txt")


def get_base_url(url: str) -> str:
    parsed_url = urlparse(url)
    base_url = parsed_url.scheme + "://" + parsed_url.netloc
    return base_url


def read_metadata_file(path: Path) -> list[dict]:
    """Read metadata file, where each line contains a JSON. These JSONs are converted to pytho dicts, and a list
    of dicts is returned. 

    Args:
        path (Path): Path to metadata file. File should contain a JSON in each line.

    Returns:
        list[dict]: List of JSONs in the metadata file, converted to List of Dictionaries. 
    """
    with path.open() as f:
        lines = f.readlines()

    metadata: list[dict] = []
    for line in lines:
        metadata.append(json.loads(line))

    return metadata


@tenacity.retry(
    retry=(tenacity.retry_if_exception_type((aiohttp.ClientConnectorError,
           aiohttp.ClientOSError, aiohttp.ServerDisconnectedError,))),
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_random(min=3, max=10))
async def download_img(session: aiohttp.ClientSession, url: str, filepath: Path):
    """Downloads the file from the provided URL asynchronously in DOWNLOAD CHUNKS. 

    Args:
        session (aiohttp.ClientSession): `aiohttp` Client session to connect to URL
        url (str): URL to the downloadable binary
        filepath (Path): Path to save the downloaded content
    """
    async with session.get(url, ssl=False) as response:
        if response.status != 200:
            raise Exception("Response was not 200")

        with open(filepath, "wb") as f:
            while True:
                chunk = await response.content.read(DOWNLOAD_CHUNK)
                await asyncio.sleep(0)  # payload not complete error
                if not chunk:
                    break
                f.write(chunk)


async def download_article_media(article: dict):
    """Download all the media of the provided article. Assign ID to each image, and map to it's article and 
    relative position in the article. 

    If download failed, Exception string is stored in the metadata. 

    - Has to be a stateless function for parallelism

    Args:
        session (aiohttp.ClientSession): Client session to connect to URLs async
        article (dict): Dictionary with article metadata
    """
    img_data_list = []

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
                "Image Path": str(article_dir/img_name),
                "Article Id": article["id"],
                "Article Index": idx,
                "Image URL": img_url,
                "Exception": ""
            }

            try:
                _ = await download_img(session, img_url, article_dir/img_name)
            except Exception as e:
                # download failed for some reason
                data["Exception"] = f"EXCEPTION:::{str(e)}"
                with EXCEPTION_FILE.open("a") as f:
                    f.write(
                        f"Exception on image: {str(data['Image Path'])}, Exception: {str(e)}, URL: {img_url}\n")
            finally:
                img_data_list.append(data)

    img_metadata_file = article_dir/"metadata.json"
    with img_metadata_file.open("w") as f:
        json.dump(img_data_list, f, indent=2)

    progress_bar.update()


async def main():
    print("reading metadata...")
    metadata = read_metadata_file(
        Path("/media/salkhon/Local Disk/Thesis/data/english.metadata"))
    print(f"metadata read, there are {len(metadata)} articles")
    # downloads will be placed in this directory
    os.chdir("/media/salkhon/Local Disk/Thesis/downloads")

    EXCEPTION_FILE.unlink(missing_ok=True)

    print("Starting downloads...")

    metadata_slice = metadata[article_slice]

    global progress_bar
    progress_bar = tqdm(total=len(metadata_slice))

    tasks = []
    for article in metadata_slice:
        task = asyncio.ensure_future(
            download_article_media(article))
        tasks.append(task)

    await asyncio.gather(*tasks)

# Run the main function
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
