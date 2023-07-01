from PIL import Image
import os
from pathlib import Path

os.chdir("/media/salkhon/Local Disk/Thesis/downloads")


if __name__ == "__main__":
    count = 0
    for fmt in ["*.jpg", "*.png", "*.gif"]:
        for img_path in Path("./").rglob(fmt):
            count += 1
            img = Image.open(img_path)
            print(count, img.size, end="\t")

    print("\nImage count:", count)
