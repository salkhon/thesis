from PIL import Image
import os
from pathlib import Path
import argparse
from tqdm import tqdm

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--imgdir", type=str,
                    help="Directory where the images will be found")

args = parser.parse_args()
IMGDIR = Path(args.imgdir)

os.chdir(IMGDIR)


if __name__ == "__main__":
    success = 0
    fail = 0

    for fmt in ["*.jpg", "*.png", "*.gif"]:
        print(f"Checking {fmt} files...")
        for img_path in tqdm(Path("./").rglob(fmt)):
            try:
                img = Image.open(img_path)
                success += 1
            except Exception as e:
                fail += 1

    print("\nImages successfully read:", success)
    print("Images failed to be read:", fail)
