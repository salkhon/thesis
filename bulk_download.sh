#!/bin/bash

# Default values
slice_len=10000
metadata="/home/salkhon/repo/Thesis/data/complete_bbc_data/media_metadata/english.metadata"
download_dir="/home/salkhon/repo/Thesis/downloads"
cooldown=$((1 * 60))
max_retry=5
start=0

# Process command-line arguments using getopts
while getopts ":s:m:d:r:c:a:" opt; do
    case $opt in
    s)
        slice_len=$OPTARG
        ;;
    m)
        metadata="$OPTARG"
        ;;
    d)
        download_dir="$OPTARG"
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
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

total_articles=$(wc -l <"$metadata")

echo -e "Will download from $metadata, \nto $download_dir, \nmedia from $total_articles articles, \nwith slices of $slice_len\nstarting from $start"

# download slice by slice
for ((start_idx = start; start_idx < total_articles; start_idx += slice_len)); do
    end_idx=$(($start_idx + $slice_len))
    if [[ $end_idx -gt $total_articles ]]; then
        end_idx=$total_articles
    fi

    python3 scripts/download/download_asyncio.py \
        --download-dir "$download_dir" \
        --metadata "$metadata" \
        --start-idx $start_idx \
        --end-idx $end_idx \
        --step 1 \
        --max-retry $max_retry

    echo "$start_idx to $end_idx complete"
    python3 scripts/exceptions/count_exceptions.py --imgdir "$download_dir"
    echo "Cooling down for $cooldown seconds"
    sleep $cooldown
done

echo -e "\n\nDOWNLOAD COMPLETE\n\n"

# run file integrity test
echo "Testing image integrity..."
python3 ./scripts/filter/read_test.py --imgdir "$download_dir"

# compile all exceptions from individual article directories
echo "Compiling exceptions..."
python3 ./scripts/exceptions/compile_exceptions.py --imgdir "$download_dir" --output "./all_exceptions.json"
