import os
from PIL import Image
import json
from pathlib import Path
import argparse
from enum import Enum
import pandas as pd
from colorama import Fore
from tqdm import tqdm

################################## argument parsing ###########################################
parser = argparse.ArgumentParser()
parser.add_argument(
    "--imgdir",
    type=str,
    default="/home/salkhon/Documents/thesis/data/images/yoruba",
    help="Directory where the images will be found",
)

args = parser.parse_args()
IMGDIR = Path(args.imgdir)
############################################################################################

LANG = IMGDIR.name


class ImageStatus(Enum):
    USEFUL = "USEFUL"
    SKIPPED = "SKIPPED"
    EXCEPTION = "EXCEPTION"
    FILTERED = "FILTERED"
    CORRUPT = "CORRUPT"
    MISSING = "MISSING"


def read_article_img_mdatas(article_dir: Path) -> tuple:
    """Read metadata associated with downloaded article.

    Args:
        article_dir (Path): Path to article directory

    Returns:
        tuple[list[dict]*3]: Tuple of list of metadata dicts: successful, skipped, exceptions
    """

    def read_downloaded_mdata(mdata_path: Path) -> list[dict]:
        mdata_dicts = []
        if mdata_path.exists():
            with mdata_path.open() as f:
                mdata_dicts = json.load(f)
        return mdata_dicts

    successful_mdata = read_downloaded_mdata(article_dir / "successful_metadata.json")
    skipped_mdata = read_downloaded_mdata(article_dir / "skipped_links.json")
    exceptions_mdata = read_downloaded_mdata(article_dir / "exceptions_metadata.json")

    return (
        successful_mdata,
        skipped_mdata,
        exceptions_mdata,
    )


def remove_json_metadata(article_dir: Path):
    (article_dir / "successful_metadata.json").unlink(missing_ok=True)
    (article_dir / "skipped_links.json").unlink(missing_ok=True)
    (article_dir / "exceptions_metadata.json").unlink(missing_ok=True)


def insert_mdata_into_df_dict(
    mdata: dict,
    df_dict: dict[str, list],
    img_status: ImageStatus,
    img_info: dict,
):
    df_dict["ImageId"].append(mdata["Id"])
    df_dict["ImageUrl"].append(mdata["Image URL"])
    df_dict["ArticleId"].append(mdata["Article Id"])
    df_dict["ArticleLang"].append(LANG)
    df_dict["ArticleIdx"].append(mdata["Article Index"])
    df_dict["ArticleUrl"].append(mdata["Article URL"])
    df_dict["ImageStatus"].append(
        img_status.value if isinstance(img_status, ImageStatus) else img_status
    )
    df_dict["ImagePath"].append(
        mdata["Image Path"]
        if img_status in (ImageStatus.USEFUL, ImageStatus.FILTERED, ImageStatus.CORRUPT)
        else None
    )

    # won't have any keys if not useful, filtered, or corrupt. Auto None appended
    df_dict["ImageFileSize"].append(img_info.get("ImageFileSize"))

    # won't have keys if not useful of filtered. Auto None appended
    df_dict["ImageFormat"].append(img_info.get("ImageFormat"))
    df_dict["ImageWidth"].append(img_info.get("ImageWidth"))
    df_dict["ImageHeight"].append(img_info.get("ImageHeight"))
    df_dict["ImageAspectRatio"].append(img_info.get("ImageAspectRatio"))


def move_img_update_mdata_path(
    old_img_path: Path, mdata: dict, img_status: ImageStatus
):
    new_img_path = (
        old_img_path.parent / img_status.value / old_img_path.name
    )  # relative to download dir
    Path(old_img_path.parent / img_status.value).mkdir(exist_ok=True)
    old_img_path.rename(new_img_path)
    mdata["Image Path"] = str(new_img_path)
    return new_img_path


def get_img_info(img_path: Path, img: Image.Image):
    return {
        "ImageFileSize": img_path.stat().st_size,
        "ImageFormat": img.format,
        "ImageWidth": img.width,
        "ImageHeight": img.height,
        "ImageAspectRatio": round(img.width / img.height, 4),
    }


def organize_article_imgs(article_dir: Path, df_dict: dict[str, list]):
    """Performs filtration of images for this article. Useful, filtered, corrupt images are moved to their
    corresponding subdirectories named: `useful`, `filtered`, `corrupt`.
    Filtration criterion:
    1. Height or width is < 150px
    2. Aspect ratio > 2 or < 0.5

    Appends metadata of this article to the `df_dict` dictionary.

    Args:
        article_dir (Path): Path to this article's directory
        df_dict: dict[str, list]: Dictionary for the images for this language, accumulated over each article
    """

    def is_filter(img: Image.Image) -> bool:
        """Filtration criterions.

        Args:
            img (Image.Image): Pillow Image

        Returns:
            bool: Whether to filter the image
        """
        w, h = img.size
        aspect = w / h
        return w < 64 or h < 64 or aspect < 0.25 or aspect > 4

    success_mdata, skipped_mdata, exceptions_mdata = read_article_img_mdatas(
        article_dir
    )

    # These images don't exist, so not image related info added, just the metadata
    for skipped_mdata in skipped_mdata:
        insert_mdata_into_df_dict(skipped_mdata, df_dict, ImageStatus.SKIPPED, {})
    for exception_mdata in exceptions_mdata:
        insert_mdata_into_df_dict(exception_mdata, df_dict, ImageStatus.EXCEPTION, {})

    # iterate over the images in this article's directory, disribute them in `useful/`, `filtered/`, `corrupted/`
    for success_mdata in success_mdata:
        img_path = Path(success_mdata["Image Path"])  # relative to download dir

        try:
            img = Image.open(img_path)
            if not img:
                raise Exception("Read image is none")
        except FileNotFoundError as _:
            # the metadata file has the same URL multiple times for some articles,
            # so they have dupicate entries that may have been already moved to`useful/`, `filtered/`, `corrupted/`

            # find if this image was previously moved (URL will match with existing records)
            try:
                idx = df_dict["ImageUrl"].index(success_mdata["Image URL"])
            except ValueError as _:
                # has not been downloaded and moved before, truly missing
                insert_mdata_into_df_dict(
                    success_mdata, df_dict, ImageStatus.MISSING, {}
                )
                continue

            # image previously moved
            success_mdata["Image Path"] = df_dict["ImagePath"][idx]
            img_info = {}
            for key in (
                "ImageFileSize",
                "ImageFormat",
                "ImageWidth",
                "ImageHeight",
                "ImageAspectRatio",
            ):
                img_info[key] = df_dict[key][idx]

            # could be success, filtered, corrupt
            insert_mdata_into_df_dict(
                success_mdata, df_dict, df_dict["ImageStatus"][idx], img_info
            )
            continue
        except:
            # image not readable, handle corrupt image
            new_img_path = move_img_update_mdata_path(
                img_path, success_mdata, ImageStatus.CORRUPT
            )
            insert_mdata_into_df_dict(
                success_mdata,
                df_dict,
                ImageStatus.CORRUPT,
                {"ImageFileSize": new_img_path.stat().st_size},
            )
            continue

        # handle filtered image
        if is_filter(img):
            new_img_path = move_img_update_mdata_path(
                img_path, success_mdata, ImageStatus.FILTERED
            )
            insert_mdata_into_df_dict(
                success_mdata,
                df_dict,
                ImageStatus.FILTERED,
                get_img_info(new_img_path, img),
            )
            continue

        # articles that survive filtration, corruption
        new_img_path = move_img_update_mdata_path(
            img_path, success_mdata, ImageStatus.USEFUL
        )
        insert_mdata_into_df_dict(
            success_mdata,
            df_dict,
            ImageStatus.USEFUL,
            get_img_info(new_img_path, img),
        )

    # replace json metadata with CSV
    remove_json_metadata(article_dir)


if __name__ == "__main__":
    total_articles = sum(1 for item in IMGDIR.iterdir() if item.is_dir())
    print(
        f"""
    Postprocess Configuration:
        Image Directory: {IMGDIR}, 
        Language: {LANG}, 
        Total Number of Articles: {total_articles}, 
    """
    )
    _ = input(Fore.YELLOW + "Press ENTER to proceed... (Ctrl+C to cancel)" + Fore.RESET)

    df_dict = {
        "ImageId": [],
        "ImageUrl": [],
        "ArticleId": [],
        "ArticleLang": [],
        "ArticleIdx": [],
        "ArticleUrl": [],
        "ImageStatus": [],
        "ImagePath": [],
        "ImageFileSize": [],
        "ImageFormat": [],
        "ImageWidth": [],
        "ImageHeight": [],
        "ImageAspectRatio": [],
    }

    os.chdir(IMGDIR)
    for item in tqdm(Path("./").iterdir(), total=total_articles):
        if item.is_dir:
            organize_article_imgs(item, df_dict)

    stat_df = pd.DataFrame(df_dict).set_index("ImageId")
    stat_df.to_csv(f"{LANG}.csv")
