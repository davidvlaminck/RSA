#!/usr/bin/env python3
"""Add a mapping from spreadsheet_id to local excel filename.

Usage:
  python scripts/add_spreadsheet_mapping.py --id <spreadsheet_id> --file "[RSA] My Report.xlsx"
"""
from pathlib import Path
import argparse
from outputs.spreadsheet_map import add_mapping

p = argparse.ArgumentParser()
p.add_argument('--id', required=True, help='spreadsheet id string')
p.add_argument('--file', required=True, help='local excel filename (relative to RSA_OneDrive)')
args = p.parse_args()

add_mapping(args.id, args.file)
print('Added mapping:', args.id, '->', args.file)

