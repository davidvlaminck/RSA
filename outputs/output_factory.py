from __future__ import annotations

import os

from outputs.excel import ExcelOutput
from outputs.google_sheets import GoogleSheetsOutput


def _resolve_output_dir(settings: dict) -> str:
    # Keep backward compatibility with both shapes:
    # - {"excel": {"output_dir": ...}}
    # - {"output": {"excel": {"output_dir": ...}}}
    out_dir = settings.get("excel", {}).get("output_dir")
    if out_dir:
        return out_dir
    return settings.get("output", {}).get("excel", {}).get("output_dir", "./out")


def make_output(name: str, *, settings: dict | None = None):
    settings = settings or {}

    force_excel_env = os.environ.get("RSA_FORCE_OUTPUT") == "Excel"
    force_excel_setting = settings.get("force_excel") is True
    if force_excel_env or force_excel_setting:
        return ExcelOutput(output_dir=_resolve_output_dir(settings))

    if name == "GoogleSheets":
        return GoogleSheetsOutput()
    if name == "Excel":
        try:
            from outputs.excel_wrapper import SingleExcelWriter

            return SingleExcelWriter.get_wrapper()
        except Exception:
            return ExcelOutput(output_dir=_resolve_output_dir(settings))
    raise ValueError(f"Unsupported output: {name}")

