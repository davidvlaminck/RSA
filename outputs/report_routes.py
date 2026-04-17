from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import quote
from typing import Optional, Union

BRUSSELS_SHAREPOINT_BASE = 'https://vlaamseoverheid.sharepoint.com/sites/AIW_AIM_BIM/AIM_BIM/RSA'
_REPORT_RE = re.compile(r'(?i)report(?P<number>\d{4})')


def extract_report_number(*values: Optional[str]) -> Optional[int]:
    for value in values:
        if not value:
            continue
        match = _REPORT_RE.search(str(value))
        if match:
            return int(match.group('number'))
    return None


def report_bucket_name(report_number: int) -> str:
    start = (int(report_number) // 100) * 100
    end = start + 99
    return f'{start:04d}-{end:04d}'


def resolve_report_output_path(
    output_dir: Union[str, Path],
    *,
    excel_filename: Optional[str] = None,
    report_name: Optional[str] = None,
    report_title: Optional[str] = None,
) -> Path:
    base = Path(output_dir)
    is_rsa_onedrive = base.name == 'RSA_OneDrive'
    if excel_filename:
        filename = Path(excel_filename).name
    elif report_title:
        filename = f'{report_title}.xlsx'
    else:
        raise ValueError('excel_filename or report_title is required')

    if excel_filename and Path(excel_filename).is_absolute():
        return Path(excel_filename)

    report_number = extract_report_number(report_name, report_title, excel_filename)
    if report_number is None:
        if not is_rsa_onedrive:
            return base / filename
        raise ValueError(f'Cannot route workbook without a report number: {filename}')
    return base / report_bucket_name(report_number) / filename


def report_sharepoint_url(
    *,
    excel_filename: Optional[str] = None,
    report_name: Optional[str] = None,
    report_title: Optional[str] = None,
    base_url: str = BRUSSELS_SHAREPOINT_BASE,
) -> Optional[str]:
    if not excel_filename:
        return None

    report_number = extract_report_number(report_name, report_title, excel_filename)
    if report_number is None:
        return None

    filename = Path(excel_filename).name
    bucket = report_bucket_name(report_number)
    return '/'.join([
        base_url.rstrip('/'),
        quote(bucket, safe=''),
        quote(filename, safe=''),
    ]) + '?web=1'





