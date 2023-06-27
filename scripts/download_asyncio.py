import asyncio
import aiohttp
from pathlib import Path, PurePath
import json
import os
from tqdm import tqdm

# there are 320722 articles
article_slice = slice(1000)

DOWNLOAD_CHUNK = 1024

progress_bar: tqdm

EXCEPTION_FILE = Path("exceptions.txt")


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


async def download_img(session: aiohttp.ClientSession, url: str, filepath: Path):
    """Downloads the file from the provided URL asynchronously in DOWNLOAD CHUNKS. 

    Args:
        session (aiohttp.ClientSession): `aiohttp` Client session to connect to URL
        url (str): URL to the downloadable binary
        filepath (Path): Path to save the downloaded content
    """
    async with session.get(url) as response:
        if response.status != 200:
            try:
                response.raise_for_status()
            except Exception as e:
                raise Exception(f"Exception in aiohttp: {str(e)}")

        with open(filepath, "wb") as f:
            while True:
                chunk = await response.content.read(DOWNLOAD_CHUNK)
                if not chunk:
                    break
                f.write(chunk)


async def download_article_media(session: aiohttp.ClientSession, article: dict):
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

    # iterate over each media of this article
    tasks = []
    for idx, img_url in enumerate(article["media_links"]):
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
        img_data_list.append(data)

        # try to download image, if not possible - will store exception string
        task = asyncio.ensure_future(download_img(
            session, img_url, article_dir/img_name))
        tasks.append(task)

    # check the results of async tasks to find and store exceptions
    for idx, result in enumerate(tasks):
        try:
            await result
        except BaseException as e:
            # download failed for some reason
            img_data_list[idx]["Exception"] = str(e)
            with EXCEPTION_FILE.open("a") as f:
                f.write(
                    f"Exception on image: {str(img_data_list[idx]['Image Path'])}\n")

    img_metadata_file = article_dir/"metadata.json"
    with img_metadata_file.open("w") as f:
        json.dump(img_data_list, f, indent=2)

    progress_bar.update()


async def main():
    print("reading metadata...")
    metadata = read_metadata_file(
        Path("/home/salkhon/repo/Thesis/data/complete_bbc_data/media_metadata/english.metadata"))
    print(f"metadata read, there are {len(metadata)} articles")
    # downloads will be placed in this directory
    os.chdir("/home/salkhon/repo/Thesis/downloads")

    print("Starting downloads...")

    metadata_slice = metadata[article_slice]

    global progress_bar
    progress_bar = tqdm(total=len(metadata_slice))

    async with aiohttp.ClientSession(trust_env=True) as session:
        tasks = []
        for article in metadata_slice:
            task = asyncio.ensure_future(
                download_article_media(session, article))
            tasks.append(task)

        await asyncio.gather(*tasks)

# Run the main function
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
