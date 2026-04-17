#!/usr/bin/env python3
"""Local-only dry run for Drive sync configuration.

This script does not call Google APIs. It validates the configured paths,
prints the effective sync settings, and inspects the local `RSA_OneDrive`
layout to help you test the sync setup safely.

Typical use:
  uv run python -m scripts.ops.dry_sync_test --settings settings_sample.json
  uv run python -m scripts.ops.dry_sync_test --settings settings_sample.json --strict
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys


repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


@dataclass(frozen=True)
class DrySyncConfig:
    settings_path: Path
    local_folder: Path
    drive_folder: str
    token_path: Path | None
    credentials_path: Path | None


def _resolve_path(value: str | None, base_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve()


def load_config(settings_path: str, *, local_folder: str | None = None, token_path: str | None = None, drive_folder: str | None = None) -> DrySyncConfig:
    settings_file = Path(settings_path).resolve()
    with open(settings_file, 'r', encoding='utf-8') as fh:
        settings = json.load(fh)

    settings_dir = settings_file.parent
    drive_cfg = settings.get('drive_sync', {}) if isinstance(settings, dict) else {}
    output_cfg = settings.get('output', {}) if isinstance(settings, dict) else {}
    excel_cfg = output_cfg.get('excel', {}) if isinstance(output_cfg, dict) else {}

    local_raw = local_folder or drive_cfg.get('local_folder') or excel_cfg.get('output_dir') or 'RSA_OneDrive'
    drive_raw = drive_folder or drive_cfg.get('drive_folder') or 'RSA'
    token_raw = token_path or drive_cfg.get('token_path')
    credentials_raw = drive_cfg.get('credentials_path') or settings.get('google_api', {}).get('credentials_path')

    return DrySyncConfig(
        settings_path=settings_file,
        local_folder=_resolve_path(local_raw, settings_dir) or (settings_dir / 'RSA_OneDrive').resolve(),
        drive_folder=str(drive_raw),
        token_path=_resolve_path(token_raw, settings_dir),
        credentials_path=_resolve_path(credentials_raw, settings_dir),
    )


def inspect_local_layout(local_folder: Path) -> dict[str, int]:
    stats = {
        'root_files': 0,
        'bucket_dirs': 0,
        'overview_files': 0,
        'summary_files': 0,
    }
    if not local_folder.exists():
        return stats

    for entry in sorted(local_folder.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            stats['bucket_dirs'] += 1
            if entry.name == 'Overzicht':
                for child in entry.iterdir():
                    if child.is_file() and child.suffix.lower() == '.xlsx':
                        stats['overview_files'] += 1
                        if child.name == '[RSA] Overzicht rapporten.xlsx':
                            stats['summary_files'] += 1
        elif entry.is_file() and entry.suffix.lower() == '.xlsx':
            stats['root_files'] += 1
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description='Local-only dry run for RSA Google Drive sync configuration')
    parser.add_argument('--settings', default=str(repo_root / 'settings_sample.json'), help='Path to settings JSON')
    parser.add_argument('--local-folder', default=None, help='Override local RSA_OneDrive path')
    parser.add_argument('--token', default=None, help='Override token path (checked locally only)')
    parser.add_argument('--drive-folder', default=None, help='Override Google Drive folder name')
    parser.add_argument('--strict', action='store_true', help='Fail if the local layout looks invalid')
    args = parser.parse_args()

    cfg = load_config(
        args.settings,
        local_folder=args.local_folder,
        token_path=args.token,
        drive_folder=args.drive_folder,
    )

    layout = inspect_local_layout(cfg.local_folder)

    print('Dry sync config:')
    print(f'  settings      : {cfg.settings_path}')
    print(f'  local_folder  : {cfg.local_folder}')
    print(f'  drive_folder  : {cfg.drive_folder}')
    print(f'  token_path    : {cfg.token_path or "<not configured>"}')
    print(f'  credentials   : {cfg.credentials_path or "<not configured>"}')
    print('Local layout:')
    print(f'  root xlsx files   : {layout["root_files"]}')
    print(f'  bucket directories : {layout["bucket_dirs"]}')
    print(f'  overview xlsx files: {layout["overview_files"]}')
    print(f'  summary workbook   : {layout["summary_files"]}')

    if args.strict:
        if layout['root_files'] > 0:
            print('ERROR: root-level .xlsx files exist in RSA_OneDrive; they should only live inside bucket folders or Overzicht.')
            return 1
        if cfg.token_path is not None and not cfg.token_path.exists():
            print(f'ERROR: token file does not exist: {cfg.token_path}')
            return 1
        if cfg.credentials_path is not None and not cfg.credentials_path.exists():
            print(f'ERROR: credentials file does not exist: {cfg.credentials_path}')
            return 1

    print('Dry sync check completed (no Google Drive API calls were made).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

