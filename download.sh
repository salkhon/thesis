#!/bin/bash
# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No color

# Default argument values
slice_len=500
metadata_filepath="/home/salkhon/Documents/thesis/data/metadata/punjabi.metadata"
img_download_dir="/home/salkhon/Documents/thesis/data/images"
cooldown=5
max_retry=3
start=0
timeout=$((5 * 60))

# Process command-line arguments using getopts
while getopts ":s:m:d:r:c:a:t:" opt; do
    case $opt in
    s)
        slice_len=$OPTARG
        ;;
    m)
        metadata_filepath="$OPTARG"
        ;;
    d)
        img_download_dir="$OPTARG"
        ;;
    r)
        max_retry=$OPTARG
        ;;
    c)
        cooldown=$OPTARG
        ;;
    a)
        start=$OPTARG
        ;;
    t)
        timeout=$OPTARG
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

total_articles=$(wc -l <"$metadata_filepath")

language=$(basename "$metadata_filepath")
language="${language%.*}"

img_download_dir="$img_download_dir/$language"

# Confirm parameters
config_str="Configurations:
\tImage Download Directory: $img_download_dir
\tMetdata File: $metadata_filepath
\tLanguage: $language
\tTotal Number of Articles: $total_articles
\tSlice Length: $slice_len
\tStart Index: $start
\tTimeout: $timeout seconds
\tMax Retry: $max_retry
\tCooldown: $cooldown seconds

${YELLOW} Press any key to proceed... (Ctrl+C to cancel) ${NC}
"
echo -e "$config_str"
read -n 1 -s -r

# create subdirectory for language
mkdir -p "$img_download_dir"

# download slice by slice
for ((start_idx = start; start_idx < total_articles; start_idx += slice_len)); do
    # make sure end_idx doesn't exceed article count
    end_idx=$(($start_idx + $slice_len))
    if [[ $end_idx -gt $total_articles ]]; then
        end_idx=$total_articles
    fi

    echo -e "\tStarting download: Start Index: $start_idx\t End Index: $end_idx\n"
    python3 scripts/download_asyncio.py \
        --download-dir "$img_download_dir" \
        --metadata "$metadata_filepath" \
        --start-idx $start_idx \
        --end-idx $end_idx \
        --step 1 \
        --max-retry $max_retry

    echo -e "\n${GREEN}\tDownload Complete: Start Index: $start_idx\t End Index: $end_idx. ${NC}"
    echo -e "${RED}\tNumber of articles with exceptions: $(find "$img_download_dir" -type f -name exceptions_metadata.json | wc -l). ${NC}"
    echo -e "\tCooling down for $cooldown seconds\n"

    if [[ $end_idx -lt $total_articles ]]; then
        sleep $cooldown
    fi
done

echo -e "${GREEN}\n\nDOWNLOAD COMPLETE\n\n ${NC}"
