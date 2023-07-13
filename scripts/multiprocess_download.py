import subprocess
import argparse
from multiprocessing import Pool
from download_asyncio import read_metadata_file
from pathlib import Path
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm
from colorama import Fore

################################## argument parsing ###########################################
parser = argparse.ArgumentParser()
parser.add_argument(
    "--download-dir",
    type=str,
    default="/home/salkhon/Documents/thesis/data/images",
    help="Path to directory where the images will be downloaded",
)
parser.add_argument(
    "--metadata-path",
    type=str,
    default="/home/salkhon/Documents/thesis/data/metadata/chinese_simplified.metadata",
    help="Path to metadata file of the article",
)
parser.add_argument(
    "--max-retry",
    type=int,
    default=3,
    help="Maximum retry count if file download fails",
)
parser.add_argument(
    "--slice-len",
    type=int,
    default=500,
    help="Number of files downloaded by a single async process",
)
parser.add_argument(
    "--timeout", type=int, default=500, help="Timeout for download request, in seconds"
)
parser.add_argument(
    "--maxproc", type=int, default=None, help="Maximum number of concurrent processes"
)


args = parser.parse_args()

DOWNLOAD_DIR = Path(args.download_dir)
METADATA_FILEPATH = Path(args.metadata_path)
MAX_RETRY = args.max_retry
SLICE_LEN = args.slice_len
TIMEOUT = args.timeout
MAXPROC = args.maxproc
############################################################################################


def execute_async_download_script(arg_dict):
    subprocess.call(
        f"""
        python3 scripts/download_asyncio.py \
        --download-dir "{arg_dict['download_dir']}" \
        --metadata "{arg_dict['metadata']}" \
        --start-idx {arg_dict['start_idx']} \
        --end-idx {arg_dict['end_idx']} \
        --step 1 \
        --max-retry {arg_dict['max_retry']} \
        --timeout {arg_dict['timeout']} \
        """,
        shell=True,
        stdout=subprocess.DEVNULL,
    )
    return (arg_dict["start_idx"], arg_dict["end_idx"])


def count_exceptions(img_dir: Path) -> int:
    count = 0
    for item in img_dir.rglob("exceptions_metadata.json"):
        if item.is_file():
            count += 1
    return count


if __name__ == "__main__":
    lang = METADATA_FILEPATH.stem
    lang_img_subdir = DOWNLOAD_DIR / lang

    mdata_dict = read_metadata_file(METADATA_FILEPATH)
    total_articles = len(mdata_dict)

    async_script_args = [
        {
            "download_dir": lang_img_subdir,
            "metadata": METADATA_FILEPATH,
            "start_idx": start_idx,
            "end_idx": min(start_idx + SLICE_LEN, total_articles),
            "max_retry": MAX_RETRY,
            "timeout": TIMEOUT,
        }
        for start_idx in range(0, total_articles, SLICE_LEN)
    ]

    num_subproc = len(async_script_args)

    print(
        f"""
    Multiprocess Download Configuration:
        Image Download Directory: {lang_img_subdir}, 
        Metadata File: {METADATA_FILEPATH}, 
        Language: {lang}, 
        Total Number of Articles: {total_articles}, 
        Slice Length: {SLICE_LEN}, 
        Timeout: {TIMEOUT}, 
        Max Retry: {MAX_RETRY}, 
        Number of Total Subprocesses: {num_subproc}
    """
    )
    _ = input(Fore.YELLOW + "Press ENTER to proceed... (Ctrl+C to cancel)" + Fore.RESET)

    lang_img_subdir.mkdir(exist_ok=True)

    with Pool(MAXPROC, initializer=tqdm.set_lock, initargs=(tqdm.get_lock(),)) as pool:
        _ = list(
            tqdm(
                pool.imap_unordered(execute_async_download_script, async_script_args),
                total=num_subproc,
                desc="TOTAL",
                position=0,
                colour="green",
                dynamic_ncols=True,
            )
        )

    # Find exception count
    articles_with_exceptions = count_exceptions(lang_img_subdir)
    print(
        Fore.RED,
        f"Number of articles with exceptions: {articles_with_exceptions}",
        Fore.RESET,
    )
    print(Fore.GREEN, f"DOWNLOAD COMPLETE FOR {lang}", Fore.RESET)
