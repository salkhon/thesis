# Bulk Download the Entire Metadata File
Use the following command to bulk download from a metadata file:
```
./download.sh \
    -s 100 \
    -m /home/salkhon/repo/Thesis/data/complete_bbc_data/media_metadata/amharic.metadata \
    -d ./abc \
    -c 20 \
    -r 3
```

Here each command flag stands for:
| Flag | Meaning |
| --- | --- |
| `-s` | Slice length. Will break down the download into this many slices with cool-down periods in between to stop the server from blocking session |
| `-m` | Path to metadata file |
| `-d` | Path to download directory |
| `-c` | Cooldown period in seconds | 
| `-r` | Maximum number of retries for a download |

This shell script will download the image files, and do a read test on them to report the number of images downloaded. It will also compile all exceptions from the image directories into the file `./all_exceptions.json`. 

# Manually Download a Slice of the Metadata File
Use the following command to download:
```
python scripts/download/download_asyncio.py --download-dir "<YOUR DIR HERE>" --metadata "<YOUR FILE HERE>" --start-idx 0 --end-idx 1000 --step 1 --max-retry 5
```