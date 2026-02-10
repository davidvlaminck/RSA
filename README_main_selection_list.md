# main_selection_list

Run a fixed selection of reports via the worker CLI, using the same settings path as `main.py` by default.

## Default behavior

Runs:
- `Report0002`
- `Report0004`
- `Report0030`
- `Report0048`

Settings path defaults to:
`/home/davidlinux/Documenten/AWV/resources/settings_RSA.json`

## Usage

Dry run (prints the command only):

```bash
python main_selection_list.py --dry-run
```

Run with defaults:

```bash
python main_selection_list.py
```

Override settings path:

```bash
python main_selection_list.py --settings /path/to/settings.json
```

Override report list:

```bash
python main_selection_list.py --reports Report0002 Report0035
```

Run in parallel by datasource (uses settings.json report_execution limits):

```bash
python main_selection_list.py --parallel
```

Parallel mode runs one pipeline per datasource concurrently (e.g., one ArangoDB pipeline and one PostGIS pipeline), so reports for each datasource run sequentially inside their pipeline.

Dry run for parallel mode:

```bash
python main_selection_list.py --parallel --dry-run
```

## Shared runner

Both `run_single_report.py` and `main_selection_list.py` use the shared runner in `lib/reports/selection_runner.py`.

To run a single report once:

```bash
python run_single_report.py --report Report0002 --once
```

To run a single report in daily loop mode:

```bash
python run_single_report.py --report Report0002
```
