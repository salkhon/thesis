from PIL import Image
import os
from pathlib import Path
import argparse

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--imgdir", type=str,
                    help="Directory where the images will be found")

args = parser.parse_args()
IMGDIR = Path(args.imgdir)


def filter_img(img_path: Path) -> bool:
    """Performs filtration of images. If the passed in image falls into a filtration criterion, it will be moved from the main directory to a filtered subdirectory.

    Filtration criterion:
    1. Height or width is < 150px
    2. Aspect ratio > 2 or < 0.5

    If the image is filtered, `successful_metadata.json` is updated with the image removed from the json. This image metadata is then
    inserted into `filtered_metadata.json`. 

    Args:
        img_path (Path): Path to image

    Returns:
        bool: Whether the image was filtered
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
    
    def update_metadata():
        pass

    img = Image.open(img_path)

    if is_filter(img):
        base_dir = img_path.parent
        filter_dir = base_dir/"filter"
        filter_dir
        pass

    return False


if __name__ == "__main__":
    os.chdir(IMGDIR)
    count = 0
    for fmt in ["*.jpg", "*.png", "*.gif"]:
        for img_path in Path("./").rglob(fmt):
            count += 1
            img = Image.open(img_path)
            # print(count, img.size, end="\t")

    print("\nImage count:", count)
