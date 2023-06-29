import json
from pathlib import Path
import os

if __name__ == "__main__":
    os.chdir("/media/salkhon/Local Disk/Thesis/downloads")

    excep_metadata_list: list[dict] = []
    for metadata_path in Path("./").rglob("*.json"):
        with metadata_path.open() as f:
            metadata_dicts = json.load(f)

        for metadata_dict in metadata_dicts:
            if metadata_dict["Exception"]:
                excep_metadata_list.append(metadata_dict)

    print("Total Exceptions: ", len(excep_metadata_list))
