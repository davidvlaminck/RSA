"""Simple smoke test: download one file from SharePoint to verify connectivity.

Run from the repo root (RSA/):
    python -m scripts.ops.sharepoint_download_test
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from API.clients.sharepoint import SharepointClient


def main() -> int:
    client = SharepointClient()

    print("=== Test access ===")
    try:
        token = client.get_access_token()
        print(f"Token length: {len(token)} - Token OK")
    except Exception as e:
        print(f"Token error: {e}")
        return 1

    library = client.get_document_library_by_name("AIMData")
    if not library:
        print("AIMData document library not found")
        return 1

    lib_id = library["id"]
    print(f"AIMData library id: {lib_id}")

    def find_first_file(parent_id: str, depth: int = 0):
        for item in client._list_children(parent_id, lib_id):
            if "file" in item:
                return item
            if "folder" in item and depth < 3:
                found = find_first_file(item["id"], depth + 1)
                if found:
                    return found
        return None

    target = find_first_file("root")
    if not target:
        print("No files found to download.")
        return 1

    out_path = Path(tempfile.gettempdir()) / target["name"]
    print(f"Downloading '{target['name']}' -> {out_path}")

    client._download_file(target["id"], out_path, lib_id)

    size = out_path.stat().st_size
    print(f"SUCCESS: downloaded {size} bytes to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())