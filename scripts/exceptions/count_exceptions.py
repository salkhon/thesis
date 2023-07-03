from pathlib import Path
import argparse

# argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("--imgdir", type=str,
                    help="Directory where the images will be found")
args = parser.parse_args()


IMGDIR = Path(args.imgdir)


def count_exceptions(img_dir: Path):
    file_count = sum(1 for _ in img_dir.rglob(
        '*exceptions_metadata.json') if _.is_file())
    return file_count


if __name__ == "__main__":
    print(f"Current Exception Count: ", count_exceptions(IMGDIR))
