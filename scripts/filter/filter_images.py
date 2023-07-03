from PIL import Image
import json
import os
from pathlib import Path
import argparse

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--imgdir", type=str,
                    help="Directory where the images will be found")

args = parser.parse_args()
IMGDIR = Path(args.imgdir)


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
        return w < 180 or h < 180 or aspect < 0.5 or aspect > 2

    successful_metadata_dicts: list[dict] = []
    filtered_metadata_dicts: list[dict] = []

    # read current metadata
    successful_metadata_file = Path(article_dir/"successful_metadata.json")
    with successful_metadata_file.open() as f:
        successful_metadata_dicts = json.load(f)

    # iterate over the images in this article's directory
    for img_data in successful_metadata_dicts:
        img_path = Path(img_data["Image Path"])  # relative to download dir
        img_name = img_path.name

        img = Image.open(img_path)

        if is_filter(img):
            # create filtered directory if none exists
            filter_dir = article_dir/"filtered"
            filter_dir.mkdir(exist_ok=True)

            # move file from current path into the filtered directory and updating path in metadata
            new_img_path = filter_dir/img_name
            img_path.rename(new_img_path)
            img_data["Image Path"] = str(new_img_path)

            # insert image metadata from to filtered metadata list
            filtered_metadata_dicts.append(img_data)

    # removing elements from `successful_metadata_dicts` if that element also exists in `filtered_metadata_dicts`
    successful_metadata_dicts = list(filter(lambda successful_img_data:
                                            all(successful_img_data["Id"] != filtered_img_data["Id"]
                                                for filtered_img_data in filtered_metadata_dicts),
                                            successful_metadata_dicts))

    with successful_metadata_file.open("w") as f:
        json.dump(successful_metadata_dicts, f, indent=2)

    with (article_dir/"filtered_metadata.json").open("w") as f:
        json.dump(filtered_metadata_dicts, f, indent=2)


if __name__ == "__main__":
    for item in IMGDIR.iterdir():
        if item.is_dir:
            filter_article_imgs(item)
