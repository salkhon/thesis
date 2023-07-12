import subprocess
import argparse
from multiprocessing import Pool
from download_asyncio import read_metadata_file
from pathlib import Path

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
    default="/home/salkhon/Documents/thesis/data/metadata/igbo.metadata",
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
    "--timeout", type=int, default=300, help="Timeout for download request, in seconds"
)
parser.add_argument(
    "--maxproc", type=int, default=6, help="Maximum number of concurrent processes"
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
    print(
        f"Spawning download process: \n\tStart Index {arg_dict['start_idx']}\t End Index: {arg_dict['end_idx']}"
    )
    subprocess.call(
        f"""
        python3 scripts/download_asyncio.py \
        --download-dir "{arg_dict['download-dir']}" \
        --metadata "{arg_dict['metadata']}" \
        --start-idx {arg_dict['start_idx']} \
        --end-idx {arg_dict['end_idx']} \
        --step 1 \
        --max-retry {arg_dict['max-retry']} \
        --timeout {arg_dict['timeout']}
        """,
        shell=True,
    )


if __name__ == "__main__":
    # Creating subdirectory for article language
    lang = METADATA_FILEPATH.stem
    lang_subdir = DOWNLOAD_DIR / lang
    lang_subdir.mkdir(exist_ok=True)

    mdata_dict = read_metadata_file(METADATA_FILEPATH)
    total_articles = len(mdata_dict)

    async_script_args = [
        {
            "download-dir": lang_subdir,
            "metadata": METADATA_FILEPATH,
            "start_idx": start_idx,
            "end_idx": min(start_idx + SLICE_LEN, total_articles),
            "max-retry": MAX_RETRY,
            "timeout": TIMEOUT,
        }
        for start_idx in range(0, total_articles, SLICE_LEN)
    ]
    with Pool(MAXPROC) as pool:
        for res in pool.imap(execute_async_download_script, async_script_args):
            print(f"Process result: {res}")
