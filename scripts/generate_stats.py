import os
from PIL import Image
import json
from pathlib import Path
import argparse
import pandas as pd
from tqdm import tqdm
from download_asyncio import read_metadata_file

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument(
    "--metadata", type=str, default="downloads/", help="Article original metadata file"
)
parser.add_argument(
    "--imgdir",
    type=str,
    default="./data/images/downloads/",
    help="Directory where the images will be found",
)
parser.add_argument(
    "--outdir",
    type=str,
    default="./",
    help="Directory where the statistics csv file will be put",
)

args = parser.parse_args()
METADATA = Path(args.metadata)
IMGDIR = Path(args.imgdir)
OUTDIR = Path(args.outdir)


def read_article_img_mdatas(article_id: str) -> tuple:
    """Read metadata associated with article.

    Args:
        article_id (str): Id of article

    Returns:
        tuple[list[dict]*5]: Tuple of list of metadata dicts: successful, skipped, exceptions, filtered, corrupted
    """

    def read_mdata(mdata_path: Path) -> list[dict]:
        mdata_dicts = []
        if mdata_path.exists():
            with mdata_path.open() as f:
                mdata_dicts = json.load(f)
        return mdata_dicts

    article_path = Path(article_id)

    successful_mdata = read_mdata(article_path / "successful_metadata.json")
    skipped_mdata = read_mdata(article_path / "skipped_links.json")
    exceptions_mdata = read_mdata(article_path / "exceptions_metadata.json")
    filtered_mdata = read_mdata(article_path / "filtered/filtered_metadata.json")
    corrupted_mdata = read_mdata(article_path / "corrupted/corrupted_metadata.json")

    return (
        successful_mdata,
        skipped_mdata,
        exceptions_mdata,
        filtered_mdata,
        corrupted_mdata,
    )


def find_idx(key: str, val: str, mdata: list[dict]) -> int:
    """Find index of `img_id` in mdata.

    Args:
        key (str): Attribute name
        val (str): Attribute value
        mdata (list[dict]): Images metadata

    Returns:
        int: Index if exists, else -1
    """
    idx = -1
    for i, md in enumerate(mdata):
        if val == md[key]:
            idx = i
            break
    return idx


def get_image_status_and_mdata(
    img_id: str,
    img_url: str,
    successful_mdata: list[dict],
    skipped_mdata: list[dict],
    exceptions_mdata: list[dict],
    filtered_mdata: list[dict],
    corrupted_mdata: list[dict],
) -> tuple[str, dict | None]:
    """Find out which metadata list the image is present in, and return the metadata. If not found, return status "M".

    Args:
        img_id (str): Image Id
        img_url (str): Image URL, to be used to check if this URL is a duplicate in this article - if so it was dropped when filtering
        successful_mdata (list[dict]): Images that have been successfully downloaded
        skipped_mdata (list[dict]): Images that have been skipped during downlaod
        exceptions_mdata (list[dict]): Images that have caused exceptions during download
        filtered_mdata (list[dict]): Images that have been filtered after download
        corrupted_mdata (list[dict]): Images that could not be read after download

    Returns:
        tuple[str, dict]: The list the image was found (or not), with the metadata itself (None if not found)
    """
    if idx := find_idx("Id", img_id, successful_mdata) >= 0:
        return "S", successful_mdata[idx]
    elif idx := find_idx("Id", img_id, skipped_mdata) >= 0:
        return "D", skipped_mdata[idx]
    elif idx := find_idx("Id", img_id, exceptions_mdata) >= 0:
        return "E", exceptions_mdata[idx]
    elif (idx := find_idx("Id", img_id, filtered_mdata) >= 0) or (
        idx := find_idx("Image URL", img_url, filtered_mdata) >= 0
    ):
        # duplicate entry in article media links that was already filtered out before, were not found,
        # and thus dropped from all metadatas, so we check for them using URL
        return "F", filtered_mdata[idx]
    elif (idx := find_idx("Id", img_id, corrupted_mdata) >= 0) or (
        idx := find_idx("Image URL", img_url, corrupted_mdata) >= 0
    ):
        return "C", corrupted_mdata[idx]
    else:
        return "M", None


if __name__ == "__main__":
    article_mdatas = read_metadata_file(METADATA)
    stat_data = {
        "Id": [],
        "ImageUrl": [],
        "ArticleId": [],
        "ArticleIdx": [],
        "ArticleUrl": [],
        "ArticleLang": [],
        "Status": [],
        "Path": [],
        "Format": [],
        "Width": [],
        "Height": [],
        "AspectRatio": [],
    }

    os.chdir(IMGDIR)
    for article_mdata in tqdm(article_mdatas):
        # read all existing image metadata for this article's images
        img_mdatas_tup = read_article_img_mdatas(article_mdata["id"])

        # iterate over each media link of this article
        for article_idx, media_url in enumerate(article_mdata["media_links"]):
            # create image id composing article id and the image's relative index in the article
            image_id = f"{article_mdata['id']}_{article_idx}"
            # find out the condition of the image, and get its metadata
            status, mdata = get_image_status_and_mdata(
                image_id, media_url, *img_mdatas_tup
            )

            # dataframe entry
            img_data = {
                "Id": image_id,
                "ImageUrl": media_url,
                "ArticleId": article_mdata["id"],
                "ArticleIdx": article_idx,
                "ArticleUrl": article_mdata["url"],
                "ArticleLang": article_mdata["lang"],
                "Status": status,  # M if not found
                "Path": None,
                "Format": None,
                "Width": None,
                "Height": None,
                "AspectRatio": None,
            }

            # if image was found
            if mdata is not None:
                img_path = mdata["Path"]
                img_data["Path"] = img_path

                # if image was not corrupted
                if status != "C":
                    img = Image.open(img_path)
                    img_data["Format"] = img.format
                    img_data["Width"] = img.width
                    img_data["Height"] = img.height
                    img_data["AspectRatio"] = img.width / img.height

            for k, v in img_data.items():
                stat_data[k].append(v)

    stat_df = pd.DataFrame(stat_data)
    stat_df.to_csv(OUTDIR / "stats.csv")
