# Excel migration — actionable steps

Purpose
-------
Short, actionable checklist to migrate report output from Google Sheets to local Excel files in `RSA_OneDrive/`.

High-level plan
---------------
- Provide a drop-in Excel writer that mirrors the Sheets wrapper API used by `DQReport`.
- Make `factories.make_output()` able to return the Excel writer when appropriate.
- Verify with unit and integration tests, then roll out for all reports.

Checklist (status tracked with checkmarks)
-----------------------------------------
1. Design / contract (spec)
   - [x] Draft `Excel_migration.md` (existing)
   - [x] Create `docs/excel_output_spec.md` describing the API contract and method signatures
     - Key functions to specify:
       - `create_workbook_if_missing(path: Path | str) -> Path`
       - `create_sheet(workbook_path: str, sheet_name: str, clear_if_exists: bool=True) -> None`
       - `write_data_to_sheet(workbook_path: str, sheet_name: str, rows: Iterable[Iterable], start_cell: str='A1') -> dict`
       - `iter_rows(workbook_path: str, sheet_name: str) -> Iterator[List]`
       - `clear_sheet_range(workbook_path: str, sheet_name: str, range: str) -> None`

2. Dependencies
   - [x] Add `openpyxl` to `requirements.txt` (already present as `openpyxl==3.1.2`)
   - [ ] Document installation / virtualenv test steps in README or docs

3. Implement `outputs/excel.py`
   - [x] Core implementation exists: `ExcelOutput` with streaming-aware `write_data_to_sheet`, `write_report`, `iter_rows`, etc.
   - [x] Add `SingleExcelWriter` wrapper (init/get_wrapper) to match SheetsWrapper pattern (implemented in `outputs/excel_wrapper.py`)
   - [ ] Add locking/atomic write strategy for concurrency (future improvement)

4. Wire up factories and `DQReport`
   - [x] `factories.make_output()` supports `'Excel'` and returns `ExcelOutput` or the singleton wrapper.
   - [x] `DQReport` updated to prefer Excel when `excel_filename` exists and to capture writer metadata (`last_output_meta`).
   - [ ] Double-check all reports: if `excel_filename` is present, ensure no other code depends on Google-only features.

5. POC: `Report0002` and `Report0030`
   - [x] `Report0002` has `excel_filename` and was used to test the Excel writer.
   - [x] `Report0030` was run and validated as part of the integration POC.
   - [x] A small integration harness was used (temporary dir) to run both reports and confirm correct files/headers.

6. Tests (pytest)
   - [x] Unit tests scaffolded for `outputs.excel` at `UnitTests/test_outputs_excel.py`.
   - [x] Unit tests executed: no failures for the targeted modules.
   - [x] Integration test executed for `Report0002` and `Report0030` (see progress below)
   - [ ] Broaden integration tests to cover more reports and edge cases.

7. Manual verification steps (operator)
   - [x] Documented in `Excel_migration.md` (already present). Add concise runnable commands to `steps_excel_migration.md`:
     - Run single report (default workdir = project root):
       ```bash
       python3 scripts/run_report_real.py --report Report0002 --skip-google
       ```
     - Or explicitly set workdir (where `RSA_OneDrive` lives):
       ```bash
       python3 scripts/run_report_real.py --workdir /path/to/projectroot --report Report0002 --skip-google
       ```
     - Verify output file exists:
       ```bash
       ls -la RSA_OneDrive | grep -i 'tlcfipoort' || true
       ```

8. Rollout and follow-ups
   - [ ] After POC & tests: roll out to all reports by relying on `excel_filename` or a config flag
   - [ ] Optional: add `lib/connectors/onedrive.py` hook to upload files after generation
   - [ ] Update README with how to toggle Google vs Excel outputs


Progress notes (actions performed)
----------------------------------
- Created `docs/excel_output_spec.md` (API contract).
- Implemented `outputs/excel.py` earlier (streaming/writer and compatibility method `write_report`).
- Added `outputs/excel_wrapper.py` providing `SingleExcelWriter.init()` and `get_wrapper()`.
- Updated `factories.py` to prefer the singleton wrapper when available; falls back to direct `ExcelOutput`.
- Updated `lib/reports/DQReport.py` to store `self.last_output_meta` with the metadata returned by the writer.
- Implemented the following fixes during POC:
  - Ensure `QueryResult.keys` is always populated by datasources (Arango and PostGIS).
  - Fix Excel header placement to match existing GoogleSheets layout (header now at expected row).
  - Make `PostGISDatasource` tolerant for test runs by attempting auto-init from `RSA_SETTINGS` when the connector was not initialized.

Test results
------------
- Unit tests for `outputs.excel` executed: no failures. (Executed with `PYTHONPATH=. pytest -q UnitTests/test_outputs_excel.py`)
- Integration test for `Report0002` and `Report0030` executed and passed (when `RSA_SETTINGS` is present). The integration run validated:
  - files are created in a temp dir
  - headers and first data rows are present
  - `last_data_update` value is read for ArangoDB from `params.finished_at` when available

Open items / next steps
-----------------------
- Implement integration tests for additional reports and edge cases (large resultsets, rows with missing keys, decimal handling).
- Wire runner scripts to call `SingleExcelWriter.init(output_dir=...)` at startup (use `settings['output']['excel']['output_dir']`). Done in `run_single_report.py` when `--once` or before loop; ensure same is applied in other runners.
- Migrate historiek/overzicht writes from Google Sheets to Excel writer (so the service can run fully offline).
- Add atomic write/lock strategy for the Excel files when running multiple workers in parallel.

If you want, I will now:
- (A) add `SingleExcelWriter.init()` calls into all runner entry points (selection runner, worker, and run_single_report variants) so Excel output is always ready, and
- (B) create broader integration test runs to validate more reports.

If you'd prefer a different ordering, tell me which item to do next.
