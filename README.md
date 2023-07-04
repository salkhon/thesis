# Vision Enhanced Large Language Models
This repo currently holds the download and filtering scripts for this project. 

# Media Download Scripts
Downloads all available media for each each article from a `.metadata` file. 


## Data Organization
In the passed in download directory, images will be organized as follows:
- Each article will have a separate directory
- Inside the directory for each article, the filtered images will be available on the top level
- After filtration the images that did not pass the filtration test, will be put inside another subdirectory  called `filtered/` inside the article's directory


## Metadata 
Each article directory contains metadata about the images for that article. These metadata are kept in JSON files. 

| Metadata File | Content |
| --- | --- | 
| `successful_metadata.json` | Images that were succesfully downloaded and passed filtering |
| `filtered_links.json` | Image URLs that were skipped during download. (URL did not end with `.jpg`, `.png`, `.gif`) |
| `exceptions_metadata.json` | Images that raised exceptions while downlading (Few, can be retried) |
| `filtered_images.json` | Images that were filtered out after download (Based on aspect ratio, and pixel count) |

For example, the download directory tree looks like this for some images:
```
.
├── news-37770534
│   ├── _92090250_khadiza_1.jpg
│   ├── _92090252_khadiza_2.jpg
│   ├── exceptions_metadata.json
│   ├── filtered
│   │  ├── 309845u30-sdgv.jpg
│   │  └── 845u30-sdgvsrgv.jpg
│   ├── filtered_links.json
│   ├── filtered_metadata.json
│   └── successful_metadata.json
├── news-38121411
│   ├── _92679309_mediaitem92679308.jpg
│   ├── exceptions_metadata.json
│   ├── filtered
│   │  └── 309845u30-sdgvsrgv.jpg
│   ├── filtered_links.json
│   ├── filtered_metadata.json
│   └── successful_metadata.json
| ...
...
```


## Bulk Download All Media From a Metadata File
Shell script available in `./bulk_download.sh`. 

Use the following command to bulk download all media from a metadata file:
```
./bulk_download.sh \
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
| `-a` | Start Index of download (Used to resume in case error occurs after a certain slice) |

This shell script will download the image files, and do a read test on them to report the number of images downloaded. It will also compile all exceptions from the article directories (`exceptions_metadata.json`) into the file `./all_exceptions.json`. 

## Manually Download a Slice of the Metadata File
Script available in `scripts/download/download_asyncio.py`. 

Use the following command to download:
```
python scripts/download/download_asyncio.py --download-dir "<YOUR DIR HERE>" --metadata "<YOUR FILE HERE>" --start-idx 0 --end-idx 1000 --step 1 --max-retry 5
```

# Filtering Script (Haven't tested yet)
Filters the data on the basis on image dimensions. Script available in `scripts/filter/filter_images.py`. 