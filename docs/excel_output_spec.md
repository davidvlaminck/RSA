Excel output spec
=================

Purpose
-------
This document specifies the public API and behavior of the `ExcelWriter` used to write report results into local Excel files.

Location & usage
----------------
- Excel files will be stored under a base directory (default: `RSA_OneDrive/`). The `ExcelWriter` constructor accepts `base_dir` to override.
- Reports will provide an `excel_filename` attribute. The full path used will be `base_dir / excel_filename`.

API contract
------------
Class: ExcelWriter(base_dir: Path | str = 'RSA_OneDrive', logger: logging.Logger | None = None)

Public methods (summary):

- create_workbook_if_missing(workbook_path: str | Path) -> Path
  - Ensure workbook exists. If not, create an empty workbook with a single sheet named 'Sheet1'. Returns the Path used.

- create_sheet(workbook_path: str | Path, sheet_name: str, clear_if_exists: bool = True) -> None
  - Ensure a worksheet with `sheet_name` exists. If it exists and `clear_if_exists` is True, clear all cells in the sheet. Otherwise create a new sheet.

- write_data_to_sheet(workbook_path: str | Path, sheet_name: str, rows: Iterable[Iterable], start_cell: str = 'A1', overwrite: bool = True, use_write_only_for_nrows: int = 10000) -> dict
  - Write rows to `sheet_name` starting at `start_cell`.
  - `rows` MAY be a generator - the function must stream when needed.
  - Return: dict with keys: `rows_written` (int), `elapsed_seconds` (float), `file` (str path)
  - Behavior: if `overwrite` True, the existing sheet contents are replaced. If `overwrite` False and sheet exists, append after the last used row.
  - For large row counts (threshold `use_write_only_for_nrows`) use `WriteOnlyWorkbook` strategy.

- iter_rows(workbook_path: str | Path, sheet_name: str) -> Iterator[List[Any]]
  - Stream rows from the sheet using `openpyxl` read-only mode and yield row values (tuples/lists of cell values). Memory efficient.

- clear_sheet_range(workbook_path: str | Path, sheet_name: str, cell_range: str) -> None
  - Clear cells in `A1:C10` style range within given sheet.

- backup_file(workbook_path: str|Path) -> Path
  - Make a timestamped backup copy of file before overwriting. Return path of backup file.

Helper functions (module-level):
- normalize_value_for_excel(val) -> Any
  - Convert Decimal to float or string, datetimes to ISO string, None to empty string, bool/number unchanged.

- column_index_to_letter(index: int) -> str
- column_letter_to_index(letter: str) -> int

Notes and expectations
----------------------
- The Excel writer should preserve header rows and column order that `DQReport` expects; the first returned row should be the header.
- Persistent-column handling: The writer should expect `persistent_column` in the report object. If present, the writer must ensure that column exists at the index `num_data_columns + 1`. If report provides `persistent_column` explicitly as a letter (e.g., 'C'), the writer should respect it, but the migration rule states we will compute the column dynamically in many cases.
- Concurrency: the writer is not safe for concurrent writers writing the same file. Implement file lock / temp file + atomic move later if needed.
- File format: `.xlsx` produced by `openpyxl`.

Error handling
--------------
- All public methods raise `ExcelWriterError` (custom exception) for unrecoverable errors such as unreadable file or permission errors.
- Calling `write_data_to_sheet` with a generator that raises should attempt to clean up partial files and raise an error; optionally keep a backup of previous file.

Testing
-------
- Unit tests must cover streaming behavior and data normalization.
- Integration tests will run a report writing to a temp folder and compare the produced `.xlsx` to a golden CSV snapshot (header + rows) to ensure parity.

Future extension hooks
----------------------
- `upload_hook(file_path: Path) -> None` to upload generated files to OneDrive/SharePoint (MS Graph). Keep interface simple so it can be passed in the constructor.

Implementation notes
--------------------
- Use `openpyxl.load_workbook(file, read_only=True)` for readers, and `openpyxl.writer.write_only.WriteOnlyWorkbook()` for large writes.
- For moderate workloads `openpyxl.Workbook()` is fine and easier to test.

Versioning & Dependencies
-------------------------
- Requires `openpyxl` (tested with 3.1.x series).


