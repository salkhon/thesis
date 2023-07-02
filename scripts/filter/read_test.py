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

os.chdir(IMGDIR)


if __name__ == "__main__":
    count = 0
    for fmt in ["*.jpg", "*.png", "*.gif"]:
        for img_path in Path("./").rglob(fmt):
            count += 1
            img = Image.open(img_path)
            # print(count, img.size, end="\t")

    print("\nImage count:", count)
