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
   - [ ] Create `docs/excel_output_spec.md` describing the API contract and method signatures
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
   - [ ] Add optional `SingleExcelWriter` wrapper (init/get_wrapper) to match SheetsWrapper pattern (recommended)
   - [ ] Add locking/atomic write strategy for concurrency (future improvement)

4. Wire up factories and `DQReport`
   - [x] `factories.make_output()` supports `'Excel'` and returns `ExcelOutput`.
   - [x] `DQReport` updated to prefer Excel when `excel_filename` exists and to capture writer metadata (`last_output_meta`).
   - [ ] Double-check all reports: if `excel_filename` is present, ensure no other code depends on Google-only features.

5. POC: `Report0002` and `Report0030`
   - [x] `Report0002` already contains `excel_filename` and was used to test the Excel writer.
   - [ ] Run `Report0030` similarly and validate its output file.
   - [ ] Create a small integration harness to run these two reports into a temp dir and validate results.

6. Tests (pytest)
   - [ ] Unit tests for `outputs/excel.py`:
       - `test_create_and_write_small` — write/readback equality
       - `test_write_streaming_large` — generator-based large write
       - `test_header_and_persistent_column` — placement of persistent column
   - [ ] Integration tests for `Report0002` and `Report0030` (run -> compare snapshot)

7. Manual verification steps (operator)
   - [ ] Documented in `Excel_migration.md` (already present). Add concise runnable commands to `steps_excel_migration.md`:
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

Immediate next steps I will take (unless you instruct otherwise)
-----------------------------------------------------------------
- Create `docs/excel_output_spec.md` (short API contract).
- Add `SingleExcelWriter` wrapper (init/get_wrapper) to `outputs/` for parity with SheetsWrapper.
- Scaffold unit tests in `UnitTests/test_outputs_excel.py` (pytest-ready).  

If you prefer a different priority, tell me which items to implement first and I'll proceed and run tests.

