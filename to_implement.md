# To Implement Later - Bucketed Report Storage and Link Routing

## Goal
Implement bucketed report storage under `RSA_OneDrive` with a maximum of 100 report files per subfolder, and ensure Drive sync, summary links, and mail links all resolve to the correct SharePoint target.

## Scope of Future Implementation
- Route each generated report file to a bucket folder by report number:
  - `0000-0099`, `0100-0199`, `0200-0299`, ...
- Keep mirror sync behavior recursive so local and remote folder trees stay aligned.
- Update summary hyperlink generation (`Overzicht`) to use canonical SharePoint URLs that include bucket folder.
- Update mail hyperlink generation to use the same canonical SharePoint URLs.

## Proposed Routing Rule
- Parse report number from `ReportXXXX`.
- Compute bucket start as `(report_number // 100) * 100`.
- Compute bucket end as `bucket_start + 99`.
- Bucket name: `f"{bucket_start:04d}-{bucket_end:04d}"`.
- Destination path: `RSA_OneDrive/<bucket>/<report_file>.xlsx`.

## Proposed Implementation Plan
1. Add a small shared path utility for bucket resolution and destination path generation.
2. Integrate this utility in Excel output write path so files are written in bucket folders.
3. Ensure sync-up and sync-down recurse through all report bucket folders.
4. Update summary link builder to consume canonical bucketed SharePoint URL.
5. Update mail template/link builder to consume the same canonical URL source.
6. Add regression tests for routing, sync traversal, summary links, and mail links.

## Suggested Touchpoints (for later coding)
- `outputs/excel.py`
- `outputs/spreadsheet_map.py`
- `outputs/summary_stager.py`
- `lib/mail/` (mail body/link construction code)
- `scripts/ops/gdrive_upload.py` (if path handling is currently flat-only)
- Any helper currently constructing report file URLs for SharePoint

## Data/Config Considerations
- Keep bucket format fixed (`NNNN-NNNN`) to avoid link churn.
- Confirm whether non-report files (`logs`, summary workbook, staged files) remain at root.
- Keep one canonical URL builder for both summary and mail to avoid divergence.

## Validation Plan (after implementation)
- Route checks:
  - `Report0000`, `Report0099` -> `0000-0099`
  - `Report0100`, `Report0199` -> `0100-0199`
  - `Report0201` -> `0200-0299`
- Sync checks:
  - New local bucket file appears in remote matching bucket folder after sync-up.
  - Remote bucket file is restored locally after sync-down.
- Link checks:
  - `Overzicht` hyperlink opens the correct SharePoint file in its bucket.
  - Mail hyperlink matches the same URL used in `Overzicht`.

## Open Decisions
- Keep existing root-level report files as-is for one transition period, or move all at once.
- Decide if bucket folders should be created lazily or pre-created.
- Decide whether bucket rule should ever be configurable (default should remain deterministic).
