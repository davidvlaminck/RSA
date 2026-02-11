# Excel migration plan

Purpose
-------
This document describes a step-by-step plan to replace live Google Sheets writes with local Excel file writes stored in `RSA_OneDrive/`, while keeping API parity with the current `SheetsWrapper` used by `DQReport`. The immediate goal is a working proof-of-concept for `Report0002` and `Report0030`, then a safe rollout to all reports.

High-level approach
-------------------
- Implement an `ExcelWriter` that offers the same high-level operations as the current Sheets wrapper (create sheet, write rows, clear ranges, iterate rows) using `openpyxl`.
- Wire factories so `DQReport` can use the Excel writer with minimal or no changes.
- Test thoroughly with unit tests and manual verification steps.

Checklist (what I'll deliver)
----------------------------
- [ ] `docs/excel_output_spec.md` with the API contract (optional intermediate file)
- [x] `Excel_migration.md` (this document)
- [ ] `requirements.txt` updated to include `openpyxl`
- [ ] `outputs/excel.py` implemented (write-only streaming where needed)
- [ ] `lib` factory changes so `make_output()` can return `ExcelWriter`
- [ ] Minimal `DQReport` adjustments (if any)
- [ ] Unit tests under `UnitTests/` for the Excel writer
- [ ] Integration test for `Report0002` and `Report0030`
- [ ] Manual test instructions (below)

Detailed steps (numbered)
-------------------------
1) Design / contract (small spec)
   - Create a short spec describing the API and expected behavior. This is a single-file spec (e.g. `docs/excel_output_spec.md`) and will include the method signatures and expected inputs/outputs.
   - Contract summary (to be reproduced in the spec):
     - `create_workbook_if_missing(path: Path | str) -> Path`
     - `create_sheet(workbook_path: str, sheet_name: str, clear_if_exists: bool=True) -> None`
     - `write_data_to_sheet(workbook_path: str, sheet_name: str, rows: Iterable[Iterable], start_cell: str='A1') -> dict`
       - Returns `{rows_written: int, elapsed_seconds: float}` and must accept generators.
     - `iter_rows(workbook_path: str, sheet_name: str) -> Iterator[List]` (read-only streaming)
     - `clear_sheet_range(workbook_path: str, sheet_name: str, range: str) -> None`
     - helpers: `normalize_value_for_excel`, `column_index_to_letter`, `column_letter_to_index`

2) Add dependency
   - Add `openpyxl` to `requirements.txt` (pin to `openpyxl==3.1.*` or the project preferred minor version).
   - Install with pip in your virtualenv for testing:

```bash
pip install -r requirements.txt
# or just:
pip install openpyxl
```

3) Implement `outputs/excel.py` (core work)
   - Implement `ExcelWriter` class that mirrors SheetsWrapper public API. Constructor accepts `base_dir: Path` (default `RSA_OneDrive`), and accepts optional config flags.
   - Provide `SingleExcelWriter` singleton (init / get_wrapper) similar to `SingleSheetsWrapper` used now.
   - Implementation notes:
     - For small writes: `openpyxl.Workbook()` is fine.
     - For large streaming writes: use `openpyxl.writer.write_only.WriteOnlyWorkbook` and `.append()` rows.
     - For reading back: use `openpyxl.load_workbook(..., read_only=True)` and `.iter_rows(values_only=True)`.
     - `write_data_to_sheet` must accept a generator and write rows in a streaming way to avoid memory blowup.
     - Ensure JSON-safe conversions: `Decimal -> float or str`, `None -> ''`, `datetime` -> ISO string or Excel date cell depending on policy.
     - Persisting a `persistent_column`: apply rule "persistent column is the column after last data column".
     - Back up existing target file before overwrite (timestamped backup in same dir) unless `overwrite=False` (configurable).

4) Wire up factories and `DQReport`
   - Update `factories.make_output()` so that when a report contains `excel_filename` (or when config forces `Excel`), the `ExcelWriter` is created and returned.
   - Keep existing Google Sheets writer available (no regression).
   - Ensure `DQReport` calls only the writer's public API methods so the switch is transparent to report code.

5) Implement sample usage for `Report0002` and `Report0030`
   - Ensure these reports have `excel_filename` set (they already do).
   - Execute the reports using the usual runner but with factories returning the Excel writer.
   - Validate Excel file content (see manual test below).

6) Unit tests and integration tests
   - Unit tests for `outputs/excel.py`:
     - `test_create_and_write_small`: create workbook, write small rows, read back via `iter_rows()`, assert equality.
     - `test_write_streaming_large`: write many rows via generator and assert file exists and number of rows matches.
     - `test_header_and_persistent_column`: ensure persistent column placement as per rules.
   - Integration tests:
     - run the `init_report()` and `run_report()` flow for `Report0002` with Excel writer targeted at a temp folder, compare output to a golden snapshot (CSV or JSON). Same for `Report0030`.
   - Use pytest. Example test commands:

```bash
pytest UnitTests/test_outputs_excel.py -q
pytest UnitTests/test_report_integration_excel.py -q
```

7) Manual verification steps (for you)
   - Precondition: `RSA_OneDrive/` exists and is writeable by the runner user.
   - Run the two reports (selection list or single-run) with the runner configured to use Excel output.
   - Open the produced files (e.g. `RSA_OneDrive/[RSA] TLCfipoorten ...xlsx`) in Excel or LibreOffice and verify:
     - First row is header and column names match the Google Sheets headers.
     - Data rows exist and sample UUIDs match those returned by the AQL query.
     - The persistent column is located one column after the data columns (for the `persistent_column` rule described earlier).
     - Re-run the same report and verify a backup is created and the new file updates correctly.

8) Rollout to all reports
   - After successful POC, change `factories.make_output()` defaulting to `Excel` when `excel_filename` is present.
   - Run all reports in a non-production environment and spot-check a handful of outputs.
   - Add optional hook to upload to OneDrive/SharePoint (new `lib/connectors/onedrive.py`) that can be called after file is written.

9) Cleanup & followups
   - Ensure `README.md` has instructions on how to switch between Google and Excel outputs.
   - Add a small admin script to back up all existing Excel files (if desired).

Edge cases and constraints
-------------------------
- Memory: use `openpyxl` write-only for large datasets. Avoid creating large in-memory lists.
- Data types: ensure Decimals and datetimes are normalized; otherwise `openpyxl` may error or produce undesirable formatting.
- Concurrency: if two parallel runners attempt to write the same Excel file, implement a simple lock mechanism (file lock or atomic rename pattern) later. For now assume single-writer per report file.
- Missing `excel_filename`: do not auto-generate names silently — either fall back to Google Sheets behavior or use a deterministic `report_name.xlsx` if you want auto file creation.

Files to create / modify
------------------------
- Create: `outputs/excel.py` (main implementation)
- Optionally create: `docs/excel_output_spec.md`
- Update: `requirements.txt` (add `openpyxl`)
- Update: `factories.py` (make_output)
- Possibly modify: `DQReport.py` (minor adjustments if writer API differences appear)
- Create: `UnitTests/test_outputs_excel.py` and `UnitTests/test_report_integration_excel.py`

Estimated timeline
------------------
- Spec & skeleton: 0.5–1 day
- Implementation & local tests: 1–2 days
- Integration verification for two reports: 0.5 day
- General rollout + tests: 1–2 days

Next action (what I will do if you approve)
-------------------------------------------
If you confirm, I will start with Step 1 and Step 2:
- Create `docs/excel_output_spec.md` (short API contract) and
- Update `requirements.txt` to include `openpyxl`.

After that I'll implement `outputs/excel.py` skeleton and the `SingleExcelWriter` wrapper and unit test scaffold. I'll run tests locally and report back with the results and the generated sample Excel files for `Report0002` and `Report0030`.

If you'd like a different ordering (for example: implement `outputs/excel.py` first), tell me which step to execute now.


---
Document generated: Feb 11, 2026

