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

9. Nog te implementeren SheetsWrapper-functionaliteit in SingleExcelWriter ("scel")

   Hieronder een genummerde lijst met functies die de huidige `outputs/sheets_wrapper.py` (Google Sheets) bood
   en die we nog moeten bijbouwen in de Excel-implementatie (`SingleExcelWriter` / `ExcelOutput`). Prioriteit en
   korte implementatie-notes zijn toegevoegd.

   1) `get_sheets_in_spreadsheet(spreadsheet_id)` — lijst met sheet-namen + metadata
      - Wat: retourneer dict met sheet-namen => properties (inclusief `gridProperties` zoals `rowCount`/`columnCount`).
      - Waarom: veel rapporten lezen `gridProperties` om max_row te bepalen.
      - Prioriteit: Hoog.

   2) `read_data_from_sheet(spreadsheet_id, sheet_name, sheetrange)`
      - Wat: reguliere leesfunctie die een lijst van rij-lijsten (rows) teruggeeft.
      - Waarom: veel reports gebruiken dit als primaire data-fetch.
      - Prioriteit: Hoog.

   3) `read_celldata_from_sheet(spreadsheet_id, sheet_name, sheetrange, return_raw_results=False)`
      - Wat: retourneer ruwe API-achtige structuur (`values`, `range`, en indien gewenst `rowData` met rich cell info, hyperlinks, formules).
      - Waarom: legacy code (Historiek/Overzicht) verwacht deze vorm voor hyperlinks en cellmetadata.
      - Opmerking: in Excel spreken we van `Cell`-objecten; map deze naar een compatibel dict-formaat.
      - Prioriteit: Hoog.

   4) `find_first_nonempty_row_from_starting_cell(spreadsheet_id, sheet_name, start_cell)`
      - Wat: zoekt de eerste niet-lege rij vanaf `start_cell` (A1-achtige notatie) en retourneert het rijnummer.
      - Waarom: wordt gebruikt om persistent-kolom en append-logica te bepalen.
      - Prioriteit: Hoog.

   5) `insert_empty_rows(spreadsheet_id, sheet_name, at_row, count)`
      - Wat: schuift rijen omlaag en maakt lege rijen op `at_row` voor `count` rijen.
      - Waarom: sommige rapporten verwachten een insert-row operatie (samen met update van formules/filters).
      - Prioriteit: Middel.

   6) `delete_sheet(spreadsheet_id, sheet_name)`
      - Wat: verwijdert een blad (of recreëert het later).
      - Waarom: Historiek implementatie verwijdert oude bladen.
      - Prioriteit: Middel.

   7) `create_sheet(spreadsheet_id, sheet_name, index=None)`
      - Wat: voegt een nieuw blad toe; kan ook op index geplaatst worden.
      - Waarom: rapporten maken nieuwe sheets (Historiek) en willen soms de locatie (index).
      - Prioriteit: Hoog.

   8) `write_data_to_sheet(spreadsheet_id, sheet_name, start_cell, data, overwrite=True)`
      - Wat: reeds aanwezig in `ExcelOutput`, maar uitbreiden:
        - ondersteuning voor formules en hyperlinks
        - batch/streaming writes met progress
        - optionele formatting (bold header, column widths)
      - Prioriteit: Hoog (basis aanwezig). Middel voor formatting/extensions.

   9) `clear_filter(spreadsheet_id, sheet_name)` en `set_filter(...)`
      - Wat: verwijder of zet filter-rijen/auto-filter op kolommen.
      - Waarom: reports clearen filters na write.
      - Implementatie: openpyxl ondersteunt auto_filter; bied eenvoudige wrapper.
      - Prioriteit: Middel.

  10) `clear_sheet_range(spreadsheet_id, sheet_name, cell_range)`
      - Wat: wis waarde(s) in het opgegeven bereik.
      - Opmerking: de ExcelOutput heeft al `clear_sheet_range(workbook_path, sheet_name, range)` — hergebruik/adapter vereist.
      - Prioriteit: Middel.

  11) `write_single_cell(spreadsheet_id, sheet_name, cell, value)`
      - Wat: schrijf 1 cel (of enkele cellen) efficiënt zonder workbook-recreatie.
      - Waarom: wordt gebruikt om laatste-synctime of enkelcelle updates te doen.
      - Prioriteit: Hoog.

  12) `update_row_by_adding_number(spreadsheet_id, sheet_name, cell, delta)` (helper)
      - Wat: helper die een cel (bv. startRow) leest, optelt met delta en terug schrijft.
      - Waarom: legacy code gebruikt `start_sheetcell.update_row_by_adding_number(len(...))`.
      - Implementatie: maak helper in SheetsCell/SingleExcelWriter die veilige read+write doet.
      - Prioriteit: Middel.

  13) `read_sheet_properties(spreadsheet_id, sheet_name)` (incl. frozen rows/cols)
      - Wat: retourneer properties zoals `frozenRowCount`, `gridProperties`, column widths.
      - Prioriteit: Laag/middel.

  14) Kolombreedte en resize (`set_column_widths`) & `freeze_panes`
      - Wat: eenvoudiger API om kolombreedtes en gefixeerde rijen te zetten.
      - Waarom: sommige rapporten willen resize/formatting; er waren bugs rond resize.
      - Prioriteit: Laag (nice-to-have) — implementatie nodig als teams willen formatting parity.

  15) Ondersteuning voor formules/hyperlinks/voorkeursformattering
      - Wat: schrijf formules (strings starting with '='), en maak hyperlinks in cellen.
      - Implementatie: openpyxl ondersteunt beide; wrapper moet detecteren en correct doorgeven.
      - Prioriteit: Middel.

  16) Append- en batch-writes (append_rows, append_with_limit)
      - Wat: efficient append zonder hele sheet in geheugen te materialiseren.
      - Prioriteit: Middel/Hoog voor grote datasets.

  17) Atomic write / file-locking
      - Wat: schrijf naar tijdelijke bestand en rename (atomic), of gebruik een file lock (portalocker) bij gelijktijdige schrijvers.
      - Waarom: vereist voor veilig parallel gebruik in productie.
      - Prioriteit: Hoog (in combinatie met parallel worker execution).

  18) Compatibele 'raw' response for `read_celldata_from_sheet` to support hyperlinks and rich cell metadata
      - Wat: in Google de raw API geeft `rowData`/`values` met `hyperlink` en `userEnteredFormat`. Voor Excel we moeten een compatibele representatie maken.
      - Prioriteit: Middel/Hoog voor Historiek & link handling.

10. Implementatie-notes & aanbevolen volgorde
   - Stap 1 (hoogste prioriteit): implementeren van `get_sheets_in_spreadsheet`, `read_data_from_sheet`, `read_celldata_from_sheet`, `create_sheet`, `write_data_to_sheet`, `write_single_cell`, `find_first_nonempty_row_from_starting_cell`.
   - Stap 2: `insert_empty_rows`, `delete_sheet`, `clear_filter`, `clear_sheet_range`, `update_row_by_adding_number`.
   - Stap 3: formatting features (`set_column_widths`, freeze panes), formula/hyperlink helpers, and `append_rows`.
   - Stap 4 (safety & scale): atomic writes, file-locking, and batch/streaming append helpers.

11. Option C (staged summaries + aggregator) — recommended for parallel workers
   - Goal: allow reports to run fully in parallel without locking by making them write small, idempotent summary messages to a staging folder. A single aggregator process will serialize updates to the shared Excel summary.
   - Why: avoids contention and keeps report runtime fast; staged files provide an audit trail and can be retried.

   Checklist to implement Option C:
   - [ ] Create a staging folder inside the output dir: `RSA_OneDrive/staged_summaries/` and an archive folder: `RSA_OneDrive/staged_summaries/processed/`.
   - [ ] Implement `outputs/summary_stager.py` with function `stage_summary_update(payload: dict, staged_dir: Path | str)` that:
         * writes payload to a temporary file (e.g. `ts_reportid_uuid.json.tmp`) and renames to `.json` atomically.
         * validates basic schema (operation + spreadsheet_id/excel_filename + sheet + payload-specific fields).
   - [ ] Modify the summary/historiek write path (in `DQReport` or the Legacy history code) to call `stage_summary_update()` instead of writing Excel directly. (We'll not change report files automatically; this gives you a toggle.)
   - [ ] Implement `scripts/aggregate_summaries.py` which:
         * scans `staged_summaries/` for ready `.json` files, sorted by filename/timestamp
         * moves each file to a `processing/` subdir to claim it (atomic rename)
         * applies the operation using `ExcelOutput` (functions: `write_data_to_sheet`, `write_single_cell`, `update_row_by_adding_number`)
         * moves processed files to `processed/` with a timestamped folder or delete/archive them
         * supports CLI options: `--staged-dir`, `--processed-dir`, `--output-dir`, `--limit`, `--dry-run`, `--verbose`
   - [ ] Add a simple retry/backoff for transient failures (e.g., file locked by another process or IO errors) — aggregator should log and move failing files to `failed/` after N attempts.
   - [ ] Add unit tests for the stager and aggregator logic (simulate payload and run aggregator in dry-run).

   Minimal payload schema examples (v1):
   - Append row (typical):
     {
       "operation": "append_row",
       "excel_filename": "[RSA] TLCfipoorten hebben een sturingsrelatie naar een Verkeersregelaar.xlsx",
       "sheet": "Resultaat",
       "row": ["uuid","naam","opmerkingen (blijvend)"],
       "meta": {"report": "Report0002", "timestamp": "2026-02-13T12:00:00Z"}
     }

   - Update single cell (last sync time):
     {
       "operation": "write_cell",
       "excel_filename": "historiek.xlsx",
       "sheet": "Historiek",
       "cell": "B3",
       "value": "2026-02-13T12:00:00Z",
       "meta": {"report": "Report0002"}
     }

   - Increment counter:
     {
       "operation": "increment_cell",
       "excel_filename": "historiek.xlsx",
       "sheet": "Historiek",
       "cell": "C5",
       "delta": 1,
       "meta": {"report": "Report0002"}
     }

   Notes:
   - The aggregator will be the only process that writes to the shared summary workbook; per-report result files remain independently written by reports.
   - This approach is safe, easy to audit, and supports retries. It also enables later migration to a DB-backed summary if desired.

12. Rollout plan for staged approach
   - [ ] Implement stager and aggregator
   - [ ] Switch historiek writer to use stager in a single non-production run and validate aggregator updates
   - [ ] Run aggregator periodically (cron/systemd) or call it at the end of report-run loop
   - [ ] Monitor `RSA_OneDrive/staged_summaries/failed/` for issues and add alerts

If you want, I can now implement both `outputs/summary_stager.py` and `scripts/aggregate_summaries.py` and provide a small example run. I'll create both files next.

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
