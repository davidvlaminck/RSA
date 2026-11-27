"""Simple smoke test: download one file from SharePoint to verify connectivity.

Run from the repo root (RSA/):
    python -m scripts.ops.sharepoint_download_test
"""
import tempfile
from pathlib import Path

from API.clients.sharepoint import SharepointClient


def main() -> int:
    client = SharepointClient()

    lib_id = client._get_default_document_library_id()
    print(f"Default document library id: {lib_id}")

    items = list(client._list_children("root", lib_id))
    files = [i for i in items if "file" in i]
    print(f"Found {len(files)} file(s) in root")

    if not files:
        print("No files found in root to download.")
        return 1

    target = files[0]
    out_path = Path(tempfile.gettempdir()) / target["name"]
    print(f"Downloading '{target['name']}' -> {out_path}")

    client._download_file(target["id"], out_path, lib_id)

    size = out_path.stat().st_size
    print(f"SUCCESS: downloaded {size} bytes to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())