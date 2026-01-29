from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GraphUploadTarget:
    """Placeholder for OneDrive/SharePoint upload target.

    We will implement this once credentials + target drive/folder conventions are finalized.
    """

    drive_id: str
    folder_path: str


class MsGraphUploader:
    name = "MsGraph"

    def __init__(self, access_token: str):
        self.access_token = access_token

    def upload_file(self, local_path: str | Path, target: GraphUploadTarget) -> None:
        raise NotImplementedError("Upload via Microsoft Graph will be implemented next.")
