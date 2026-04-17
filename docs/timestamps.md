Timestamp types used by the report service

Overview
--------
This document explains the two distinct timestamps used throughout the reporting
pipeline and where each is sourced, normalized and written. All timestamps are
stored and displayed in Brussels time (`Europe/Brussels`).

1) "Report created" timestamp (created-at)
-----------------------------------------
- Purpose: records when the report run created the report file. It documents the
  moment the report was executed and the output file was generated.
- Where it is set: in `lib/reports/DQReport.py` as `self.now`.
- Format: Brussels time, formatted as `YYYY-MM-DD HH:MM:SS` (no timezone suffix).
- Usage / written to:
  - First metadata row on each report's `Resultaat` sheet: "Rapport gemaakt op {now} met data uit:".
  - Included in the `Historiek` staging payload (first column) when staging historiek rows.
- Source / semantics: produced by the report runner at report time using
  `datetime.now(ZoneInfo("Europe/Brussels")).strftime("%Y-%m-%d %H:%M:%S")`.

2) "Datasource last synchronized" timestamp (last_data_update)
-------------------------------------------------------------
- Purpose: authoritative timestamp indicating when the underlying datasource
  (ArangoDB or PostGIS) had its data last synchronized. This is used to show
  the freshness of the data the report is based on.
- Where it is discovered:
  - ArangoDB: `datasources/arango.py` attempts to obtain a timestamp in this
    order: (a) `cursor.last_data_update` (if driver/cursor exposes it), (b) the
    `params` collection `finished_at` (or other keys such as `last_data_update`,
    `last_sync`, `updated_at`), (c) inference from returned rows matching
    common date/time attribute names.
  - PostGIS: prefer a per-report `last_update_query` if configured; otherwise
    the PostGIS adapter should return a deterministic timestamp (e.g. a
    dedicated params table or explicit query). Historically PostGIS sometimes
    fell back to `datetime.now()`, which is NOT correct for freshness reporting.
- Format: Normalized to Brussels time and written as `YYYY-MM-DD HH:MM:SS`
  (no timezone suffix) when staged for the summary/historiek or when written
  to `Overzicht` column C. The aggregator further ensures normalization before
  applying writes.
- Usage / written to:
  - Second metadata row on each report's `Resultaat` sheet: e.g.
    "ArangoDB, laatst gesynchroniseerd op {last_data_update}".
  - Historically / Historiek sheet: second column contains the last_data_update
    as staged by the report (normalized) and appended via the aggregator.
  - `Overzicht` sheet column C: receives the `last_data_update` (normalized
    Brussels `YYYY-MM-DD HH:MM:SS`) for the corresponding report row. The
    aggregator consolidates multiple staged writes for the same Overzicht cell
    and applies the most recent timestamp.
- Semantics and normalization:
  - Timestamps coming from the database or driver may be:
    - timezone-aware datetimes, naive datetimes, ISO strings (with Z or offset),
      or other textual formats.
    - The code normalizes these to timezone-aware Brussels datetimes and formats
      them as `YYYY-MM-DD HH:MM:SS` for storage in `Overzicht` and `Historiek`.
  - If a report configures `last_update_query`, its (first) result value is
    preferred and normalized by `DQReport` before staging.

Common causes of incorrect Overzicht values
------------------------------------------
- Multiple parallel report runs where older staged payloads overwrite newer
  ones: the aggregator groups writes for the same workbook/sheet/cell and
  consolidates them by taking the latest timestamp before applying a single
  write. This prevents races in normal operation, but if staging files are
  created in different locations (different working dirs) the aggregator may not
  see them.
- Staged payloads written to the wrong `RSA_OneDrive` path (relative vs
  absolute): the aggregator and the staging helper resolve relative paths
  against the repository root to ensure a single canonical `RSA_OneDrive` is
  used. If scripts or manual staging used absolute or different paths, those
  staged files won't be processed by the aggregator that operates on the
  canonical folder.
- Datasource adapter not returning a last_data_update: the aggregator will
  see an empty or fallback value and write an empty cell. Ensure the Arango
  `params` collection contains `finished_at` (ISO string) or that the report
  provides a `last_update_query` returning a precise timestamp.

Developer guidance / checklist
------------------------------
- When writing report code or datasource adapters:
  - Always populate `QueryResult.last_data_update` with a normalized Brussels
    string if possible. If unavailable, prefer an empty string over
    `datetime.now()`.
  - If a per-report `last_update_query` is used, normalize the returned value
    to Brussels time before assigning to `self.last_data_update`.
- For scripts that stage payloads or run the aggregator:
  - Use relative paths (e.g. `RSA_OneDrive`) and let the code resolve them
    against the repository root, or pass absolute paths consistently.
  - Call the aggregator with the same `output-dir` used by report runs so it
    resolves the same `RSA_OneDrive` folder and finds the staged JSON files.

Quick troubleshooting steps
---------------------------
1. Verify staged payloads exist in the canonical directory:
   - ls -l RSA_OneDrive/staged_summaries
2. Inspect a staged payload for an Overzicht write and confirm its `value`:
   - jq . somefile.json
3. Run the aggregator manually pointing to the project-root-relative paths:

```bash
python scripts/ops/aggregate_summaries.py --staged-dir RSA_OneDrive/staged_summaries --output-dir RSA_OneDrive
```

4. Open `RSA_OneDrive/Overzicht/[RSA] Overzicht rapporten.xlsx` and confirm column C
   updated. If the file modified is different, inspect `outputs/spreadsheet_map.py`
   to ensure the spreadsheet_id -> filename mapping is correct.
