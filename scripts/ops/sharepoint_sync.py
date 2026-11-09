"""SharePoint sync helpers mirroring Google Drive upload/download for RSA."""
import os
from pathlib import Path

from API.clients.sharepoint import SharepointClient


def _client():
    return SharepointClient(
        client_id=os.getenv("SHAREPOINT_CLIENT_ID"),
        tenant_id=os.getenv("SHAREPOINT_TENANT_ID"),
        site_url=os.getenv("SHAREPOINT_SITE_URL"),
        client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET"),
    )


def _aimdata_library_id(client):
    lib = client.get_document_library_by_name("AIMData")
    if not lib:
        raise RuntimeError("AIMData document library not found")
    return lib["id"]


def sync_local_to_sharepoint(local_folder: str | Path) -> bool:
    client = _client()
    ok, _ = client.validate_local_mirror(local_folder)
    if not ok:
        return False
    lib_id = _aimdata_library_id(client)
    return client.sync_local_to_library(local_folder, "RSA", lib_id)


def sync_sharepoint_to_local(local_folder: str | Path) -> bool:
    """Download SharePoint RSA folder to local mirror."""
    client = _client()
    ok, _ = client.validate_local_mirror(local_folder)
    if not ok:
        return False
    lib_id = _aimdata_library_id(client)
    return client.sync_library_to_local("RSA", local_folder, lib_id)


def download_before_run(local_folder: str | Path) -> bool:
    """Download SharePoint RSA folder to local mirror before running reports."""
    return sync_sharepoint_to_local(local_folder)


def write_daily_run_log(local_folder: str | Path, status: str, details: str = "") -> None:
    client = _client()
    message = f"{status} ({details})" if details else status
    client.write_daily_run_log(local_folder, message)


def prune_daily_run_logs(local_folder: str | Path, keep: int = 14) -> None:
    client = _client()
    client.prune_daily_run_logs(local_folder, keep=keep)
