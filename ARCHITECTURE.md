# Report Runner Architecture

**Date:** 2026-02-06  
**Version:** Step 3 - Refactored for code reuse

## Overview

Three entry points now share a unified execution engine with minimal duplication:

1. **`main.py`** - ReportLoopRunner (all reports, scheduled daily)
2. **`run_single_report.py`** - Single report runner (with daily loop or --once mode)
3. **`main_selection_list.py`** - Selection list runner (4 test reports)

All three use the same shared logic in `lib/reports/selection_runner.py` and `lib/reports/pipeline_runner.py`.

---

## Execution Modes

### Sequential Mode (Default)
- Reports run **in-process** one at a time
- Singletons shared across reports
- Fast for small lists, suitable for development
- Each report can modify shared state

### Parallel-by-Datasource Mode
- Reports run in **separate subprocesses** (worker processes)
- One **pipeline per datasource** (ArangoDB, PostGIS, Neo4j)
- Multiple pipelines run **concurrently**
- Full process isolation and timeout protection
- Each process reinitializes DB connections once
- Suitable for production (respects 8GB RAM limit)

**Enable in settings.json:**
```json
{
  "report_execution": {
    "mode": "parallel_by_datasource",
    "max_concurrent": 2,
    "timeout_seconds": 1800
  }
}
```

---

## Shared Code Structure

### Core Modules

#### `lib/reports/selection_runner.py`
**Purpose:** Main entry point for running a list of reports

```python
def run_selection(
    settings_path: str,
    report_names: list[str],
    *,
    force_parallel: bool | None = None,
    stream_output: bool = True,
) -> int:
```

- Dispatches to sequential or parallel mode
- Respects `settings.json` by default
- Can force mode with `force_parallel` argument
- Returns 0 on success, 1 on failure

#### `lib/reports/pipeline_runner.py`
**Purpose:** Run pipelines per datasource concurrently

```python
def run_pipelines_by_datasource(
    report_names: Iterable[str],
    settings: dict,
    settings_path: str,
    *,
    stream_output: bool = True,
) -> int:
```

- Groups reports by datasource
- Spawns one worker subprocess per pipeline
- Manages concurrent execution with `ThreadPoolExecutor`
- Each worker reuses connections within its pipeline
- Returns 0 on success, 1 if any pipeline fails

#### `lib/reports/ReportLoopRunner.py` (Enhanced)
**Methods:**

- `run()` - Dispatches to sequential or parallel mode (all reports)
- `run_selected(report_names: list[str])` - Runs a specific list
- `_run_sequential(report_names=None)` - In-process execution
- `_run_parallel_by_datasource(report_names=None)` - Subprocess pipelines

#### `lib/reports/worker.py`
**Purpose:** Subprocess worker for isolated report execution

```python
python -m lib.reports.worker --reports Report0002 Report0004 --settings settings.json
```

- Accepts multiple reports via `--reports`
- Initializes DB connections once per worker
- Logs with report name in context for clarity
- Reuses connections for all reports in the same worker
- Exits with status code 0/1

---

## Entry Point Behaviors

### 1. main.py (Full Loop Runner)

```bash
python main.py
```

**Features:**
- Runs **all 194+ reports** from Reports/ directory
- Respects time window (config: `settings.json` → `time.start/end`)
- Continuous loop checking daily boundary
- Calls `ReportLoopRunner.run()` when time window matches

**Code:**
```python
reportlooprunner = ReportLoopRunner(settings_path=r'...settings_RSA.json')
reportlooprunner.start(run_right_away=True)
```

---

### 2. run_single_report.py (Single Report)

```bash
# Run once and exit (for testing)
python run_single_report.py --once --report Report0002

# Run in daily loop (like main.py but for one report)
python run_single_report.py --report Report0002

# Override settings
python run_single_report.py --once --report Report0035 --settings /path/to/settings.json
```

**Features:**
- Runs a **single report** (default: Report0002)
- `--once`: Execute once and exit
- Without `--once`: Daily loop like main.py
- Uses shared `run_selection()` for execution

**Code:**
```python
def run_daily(settings_path, report):
    while True:
        now = datetime.now(UTC)
        if started_running_date is None or started_running_date != now.date():
            return run_selection(settings_path=settings_path, report_names=[report])
        time.sleep(60)
```

---

### 3. main_selection_list.py (Selection)

```bash
# Run with defaults (4 reports)
python main_selection_list.py

# Force parallel mode
python main_selection_list.py --parallel

# Force sequential mode
python main_selection_list.py --parallel false

# Custom reports
python main_selection_list.py --reports Report0002 Report0035

# Dry run
python main_selection_list.py --dry-run
```

**Features:**
- Runs a **curated list** of 4 reports for testing
- Auto-detects mode from settings.json
- Can override with `--parallel`
- Easy to modify `DEFAULT_REPORTS` list

**Code:**
```python
DEFAULT_REPORTS = [
    "Report0002",   # ArangoDB
    "Report0004",   # ArangoDB
    "Report0030",   # PostGIS
    "Report0048",   # PostGIS (complex)
]
```

---

## Database Connection Strategy

### Sequential Mode (In-Process)
- **Singletons initialized once** in `ReportLoopRunner.__init__`
- All reports share the same connections
- Fast but not isolated

### Parallel Mode (Subprocess)
- **Each worker reinitializes** singletons in `lib/reports/worker.py`
- `run_reports()` calls `reinitialize_database_connections()` once at pipeline start
- All reports in the same worker **reuse the same connections**
- Each worker process has its own connection pool
- Safe for concurrent execution

**Reinitialization logic:**
```python
def run_reports(report_names: list[str], settings: dict) -> int:
    """Reinitialize DB connections ONCE at the start of the pipeline."""
    logging.info(f"Pipeline starting with {len(report_names)} reports")
    reinitialize_database_connections(settings)  # ← Once per pipeline
    
    for report_name in report_names:
        exit_code = run_single_report(report_name, settings, skip_db_init=True)
        # ↑ skip_db_init=True prevents re-init for subsequent reports
```

---

## Logging

All log lines include report name for clarity:

```
[Worker 91770] [Report0002] 2026-02-06 16:32:20 - INFO - Starting report
[Worker 91770] [Report0002] 2026-02-06 16:32:20 - INFO - Initialized
[Worker 91770] [Report0002] 2026-02-06 16:32:20 - INFO - ✓ Completed successfully
[Worker 91770] [Report0004] 2026-02-06 16:32:21 - INFO - Starting report
```

**Context tracking:**
- Python `ContextVar` used to track current report per thread/process
- Custom `ReportContextFilter` injects report name into every log record
- Enables easy grep/filtering: `grep "[Report0002]" logs.txt`

---

## Performance & Resource Usage

### Sequential Mode
- **Memory:** ~1.5-2 GB
- **Time:** ~6-8 hours for 194 reports
- **Overhead:** Minimal (no subprocess spawning)

### Parallel Mode (2 concurrent pipelines)
- **Memory:** ~4-5 GB peak (safe for 8GB)
- **Time:** ~3-4 hours for 194 reports (2x speedup)
- **Overhead:** Subprocess creation + DB re-init
- **Benefit:** Timeouts, isolation, concurrent DB access

---

## Testing Checklist

✅ **main.py**
```bash
python main.py
# Runs all reports respecting time window
```

✅ **run_single_report.py**
```bash
python run_single_report.py --once --report Report0002
# Run once and exit
```

✅ **main_selection_list.py**
```bash
python main_selection_list.py --dry-run
# Show execution mode and settings
```

✅ **Parallel mode**
```bash
python main_selection_list.py --parallel
# Runs 2 pipelines concurrently (ArangoDB + PostGIS)
```

---

## Code Reuse Summary

| Component | main.py | run_single_report.py | main_selection_list.py |
|-----------|---------|----------------------|------------------------|
| Settings parsing | ReportLoopRunner | selection_runner | selection_runner |
| Report discovery | ReportLoopRunner | selection_runner | selection_runner |
| Sequential exec | ReportLoopRunner._run_sequential | selection_runner | selection_runner |
| Parallel exec | ReportLoopRunner._run_parallel_by_datasource | selection_runner | selection_runner |
| Worker spawning | pipeline_runner | pipeline_runner | pipeline_runner |
| Shared lines | ~150 in ReportLoopRunner | ~25 custom | ~25 custom |

**Key insight:** All three entry points now use the same ~150 lines of logic in `selection_runner.py` and `pipeline_runner.py`. The only differences are CLI arguments and scheduling logic (e.g., daily loop).

---

## Future Enhancements

1. **Registry decorator (Step 2):** Allow reports to register themselves instead of relying on filename==classname
2. **Web UI:** Add a lightweight web interface to trigger reports on-demand
3. **Metrics:** Collect timing and success rate per report
4. **Retry logic:** Implement exponential backoff for failed reports
5. **Caching:** Cache report results for fast reruns

---

## Debugging

Enable detailed logging in workers:

```bash
# Stream worker output directly (no capturing)
python run_single_report.py --once --report Report0002
# All worker logs appear in real-time

# Grep by report name
grep "[Report0002]" logs.txt

# Monitor both stdout and file logs
python main_selection_list.py | tee -a logs.txt
```

---

## Summary

✅ **Three entry points, one engine**  
✅ **Minimal code duplication**  
✅ **Sequential and parallel modes**  
✅ **Full process isolation in parallel mode**  
✅ **Clean logging with report names**  
✅ **Memory-safe for 8GB systems**  
✅ **Timeout and fault tolerance**  
✅ **Easy to test and debug**
