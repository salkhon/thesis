import os
from PIL import Image
import json
from pathlib import Path
import argparse

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument(
    "--imgdir", type=str, help="Directory where the images will be found"
)

args = parser.parse_args()
IMGDIR = Path(args.imgdir)


def write_dict_to_json_file(json_file: Path, data_dicts: list[dict]):
    """Write data dict to JSON file.

    Args:
        json_file (Path): JSON file path
        data_dicts (list[dict]): List of dictionaries
    """
    with json_file.open("w") as f:
        json.dump(data_dicts, f, indent=2)


def move_img_file(img_data: dict, img_path: Path, subdir_name: str):
    """Move images to a subdirectory named `subdir_name`. Updates `img_data` dict with
    new path.

    Args:
        img_data (dict): Image metadata dict
        img_path (Path): Path to image
        subdir_name (str): Name of the subdirectory to move the image to
    """
    img_name = img_path.name
    subdir_path = img_path.parent / subdir_name

    # make subdir if none exists
    subdir_path.mkdir(exist_ok=True)

    # move file
    new_img_path = subdir_path / img_name
    img_path.rename(new_img_path)
    img_data["Image Path"] = str(new_img_path)


def filter_article_imgs(article_dir: Path):
    """Performs filtration of images for this article. If any image in this articles's directory fails the filtration criterion, it
    is moved to another subdirectory named `filtered/`. The metadata of that image is moved from `successful_metadata.json` to
    `filtered_metadata.json`.
    Filtration criterion:
    1. Height or width is < 150px
    2. Aspect ratio > 2 or < 0.5

    Args:
        article_dir (Path): Path to this article's directory
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

    # metadata to keep
    successful_metadata_dicts: list[dict] = []
    corrupted_metadata_dicts: list[dict] = []
    filtered_metadata_dicts: list[dict] = []

    # removed the filtered, corrupted, duplicates
    new_successful_metadata_dicts: list[dict] = []

    # read article metadata
    successful_metadata_file = Path(article_dir / "successful_metadata.json")
    with successful_metadata_file.open() as f:
        successful_metadata_dicts = json.load(f)

    # iterate over the images in this article's directory
    for img_data in successful_metadata_dicts:
        img_path = Path(img_data["Image Path"])  # relative to download dir

        try:
            img = Image.open(img_path)
            if not img:
                raise Exception("Read image is none")
        except FileNotFoundError as _:
            # the metadata file has the same URL multiple times for some articles,
            # so they have dupicate entries that may have been already filtered, or moved to corrupted
            # not rentering them in `new_successful_metadata_dicts`
            continue
        except:
            # handle corrupted image
            move_img_file(img_data, img_path, "corrupted")
            corrupted_metadata_dicts.append(img_data)
            continue

        # handle filtered image
        if is_filter(img):
            move_img_file(img_data, img_path, "filtered")
            filtered_metadata_dicts.append(img_data)
            continue

        # articles that survive filtration, corruption, and duplication tests
        new_successful_metadata_dicts.append(img_data)

    write_dict_to_json_file(successful_metadata_file, new_successful_metadata_dicts)
    if len(corrupted_metadata_dicts) > 0:
        write_dict_to_json_file(
            article_dir / "corrupted/corrupted_metadata.json", corrupted_metadata_dicts
        )
    if len(filtered_metadata_dicts) > 0:
        write_dict_to_json_file(
            article_dir / "filtered/filtered_metadata.json", filtered_metadata_dicts
        )


if __name__ == "__main__":
    os.chdir(IMGDIR)
    for item in Path("./").iterdir():
        if item.is_dir:
            filter_article_imgs(item)
