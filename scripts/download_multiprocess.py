from multiprocessing import Pool
import json
from pathlib import Path, PurePath
from tqdm import tqdm
import os
import requests

# there are 320722 articles
article_slice = slice(1000)

POOL_SIZE = 100
CHUNK_SIZE = 20


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


def download_img(url: str, path: Path):
    """Download the image from the provided URL and store it in the given path. 

    Args:
        url (str): URL to the image
        path (Path): Path the image is to be saved
    """
    resp = requests.get(url)
    with path.open("wb") as f:
        f.write(resp.content)


def download_article_media(article: dict):
    """Download all the media of the provided article. Assign ID to each image, and map to it's article and 
    relative position in the article. 

    If download failed, Exception string is stored in the metadata. 

    - Has to be a stateless function for parallelism

    Args:
        article (dict): Dictionary with article metadata
    """
    img_data_list = []

    article_dir = Path(article["id"])
    article_dir.mkdir(exist_ok=True)

    # iterate over each media of this article
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

        # try to download image, if not possible store exception string
        try:
            download_img(img_url, article_dir/img_name)
        except Exception as e:
            data["Exception"] = str(e)
            print(f"Exception on article: {article['id']}, image: {img_name}")
        finally:
            img_data_list.append(data)

    img_metadata_file = article_dir/"metadata.json"
    with img_metadata_file.open("w") as f:
        json.dump(img_data_list, f, indent=2)


if __name__ == "__main__":
    print("reading metadata...")
    metadata = read_metadata_file(
        Path("/home/salkhon/repo/Thesis/data/complete_bbc_data/media_metadata/english.metadata"))
    print(f"metadata read, there are {len(metadata)} articles")
    # downloads will be placed in this directory
    os.chdir("/home/salkhon/repo/Thesis/downloads")

    print("Starting downloads...")

    metadata_slice = metadata[article_slice]
    with Pool(POOL_SIZE) as p:
        for _ in tqdm(p.imap_unordered(download_article_media, metadata_slice, chunksize=CHUNK_SIZE), total=len(metadata_slice)):
            pass
