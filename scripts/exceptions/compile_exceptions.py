import json
from pathlib import Path
import os

DUMP_PATH = Path("/media/salkhon/Local Disk/Thesis/all_exceptions.json")


def get_all_exceptions_data() -> list[dict]:
    """Walk the `downloads/` directory and read all exceptions metadata and compile them in a list of dicts.

    Returns:
        list[dict]: List of dict of all exception metadata
    """
    excep_metadata_list: list[dict] = []
    for metadata_path in Path("./").rglob("*exceptions_metadata.json"):
        with metadata_path.open() as f:
            metadata_dicts: list[dict] = json.load(f)
        excep_metadata_list.extend(metadata_dicts)
    return excep_metadata_list


if __name__ == "__main__":
    os.chdir("/media/salkhon/Local Disk/Thesis/downloads")
    exceptions_metadata_list = get_all_exceptions_data()
    print("Total Exceptions: ", len(exceptions_metadata_list))

    with DUMP_PATH.open("w") as f:
        json.dump(exceptions_metadata_list, f, indent=2)
