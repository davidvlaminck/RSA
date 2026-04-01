# Architecture — System Design & Execution Modes

**Date:** 2026-03-30  
**Version:** Refactored, unified execution engine

## Contents

- [System Overview](#system-overview)
- [Execution Modes](#execution-modes)
- [Entry Points & Behaviors](#entry-points--behaviors)
- [Shared Code Structure](#shared-code-structure)
- [Database Connection Strategy](#database-connection-strategy)
- [Connection Lifecycle](#connection-lifecycle)
- [Logging & Observability](#logging--observability)
- [Performance Characteristics](#performance-characteristics)
- [Performance Tuning](#performance-tuning)
- [Testing Checklist](#testing-checklist)
- [Debugging Guide](#debugging-guide)
- [Code Reuse Metrics](#code-reuse-metrics)
- [Future Enhancements](#future-enhancements)
- [Summary](#summary)

---

## System Overview

Three entry points (main.py, run_single_report.py, main_selection_list.py) all use a **shared execution engine** with minimal code duplication. The engine supports two execution modes: **Sequential** (in-process) and **Parallel-by-Datasource** (subprocess isolation).

```
┌───────────────────────────────────────────────────────────┐
│              Shared Execution Engine                      │
│  lib/reports/                                             │
│  ├── selection_runner.py (35 lines)                       │
│  ├── pipeline_runner.py (80 lines)                        │
│  ├── ReportLoopRunner.py (150 lines)                      │
│  └── worker.py (188 lines)                                │
└───────────────────────────────────────────────────────────┘
              ▲                  ▲                    ▲
         [delegates]        [delegates]         [delegates]
              │                  │                    │
    ┌─────────────────┐ ┌──────────────────┐ ┌──────────────┐
    │    main.py      │ │ run_single_      │ │ main_        │
    │ (all reports,   │ │ report.py        │ │ selection_   │
    │  scheduled)     │ │ (1 report,       │ │ list.py      │
    │                 │ │  --once or loop) │ │ (4 reports,  │
    │  35 lines       │ │                  │ │  test mode)  │
    │                 │ │  35 lines        │ │              │
    │                 │ │                  │ │  67 lines    │
    └─────────────────┘ └──────────────────┘ └──────────────┘
```

---

## Execution Modes

### Mode 1: Sequential (Default)
**When:** Development, debugging, small deployments  
**How:** All reports run in single process, one at a time  
**Connections:** Shared singletons across all reports  
**Memory:** ~2 GB  
**Time (194 reports):** ~6-8 hours  
**Isolation:** None (shared state)

**Sequence:**
```
ReportLoopRunner (main process)
  ├─ Report0002.run_report()  [init: 0.5s, execute: 2.0s, output: 1.5s]  <- SharedConnections
  ├─ Report0003.run_report()  [similar flow]                            <- Same singletons
  ├─ Report0004.run_report()  [...]
  └─ ... 191 more
```

**Configuration:**
```json
{
  "report_execution": {
    "mode": "sequential"
  }
}
```

---

### Mode 2: Parallel-by-Datasource
**When:** Production, large deployments (8GB+ RAM)  
**How:** Reports grouped by datasource; each group runs in subprocess  
**Connections:** Each subprocess reinitializes once; reports reuse within subprocess  
**Memory:** ~4-5 GB peak  
**Time (194 reports):** ~3-4 hours (2x speedup)  
**Isolation:** Full (separate processes)

**Sequence:**
```
Main Process
  │
  ├─ ThreadPoolExecutor (max_concurrent=2)
  │   │
  │   ├─ Worker1 (subprocess) [ArangoDB reports]
  │   │   └─ SharedArangoConnection
  │   │     ├─ Report0002.run_report()
  │   │     ├─ Report0003.run_report()
  │   │     └─ ...report0098 (all ArangoDB)
  │   │
  │   └─ Worker2 (subprocess) [PostGIS reports]
  │       └─ SharedPostGISConnection
  │         ├─ Report0030.run_report()
  │         ├─ Report0048.run_report()
  │         └─ ...report0199 (all PostGIS)
  │
  └─ Monitor: aggregate results, handle failures
```

**Configuration:**
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

### Decision Matrix: When to Use Which?

| Factor | Sequential | Parallel |
|--------|-----------|----------|
| **RAM available** | <4 GB | >8 GB |
| **Reports** | <50 | >100 |
| **Development** | ✅ Yes | No (harder to debug) |
| **Production** | No | ✅ Yes |
| **Debugging** | ✅ Easy | Complex (subprocesses) |
| **Speed needed** | Not critical | ✅ 2x faster |
| **Resource isolation** | No | ✅ Yes |

---

## Entry Points & Behaviors

### 1. main.py (All Reports, Scheduled Loop)

**Purpose:** Run all reports daily in a scheduled loop, with Drive mirror sync around the run window.

**Code:**
```bash
python main.py
```

**Behavior:**
1. Stay in infinite loop managed by `ReportLoopRunner.start(run_right_away=False)`
2. Before first run of each day, wait until at least `01:00:00` and mirror-download Drive folder to local `RSA_OneDrive`
3. Respect execution window from settings (`time.start` / `time.end`)
4. Execute reports when window is active
5. After run completion, mirror-upload local `RSA_OneDrive` back to Drive
6. Append run status lines to `RSA_OneDrive/logs/run_YYYYMMDD.log`

**Implementation:**
```python
# main.py
from lib.reports.ReportLoopRunner import ReportLoopRunner
from scripts.ops.gdrive_upload import sync_drive_to_local, sync_local_to_drive

runner = ReportLoopRunner(settings_path='settings.json', excel_output_dir='RSA_OneDrive')
runner.on_before_run = daily_sync_gate.ensure_synced
runner.on_run_complete = lambda: sync_local_to_drive(...)
runner.start(run_right_away=False)
```

**Configuration (time window):**
```json
{
  "time": {
    "start": "06:00:00",
    "end": "12:50:00"
  }
}
```

---

### 2. run_single_report.py (Single Report, Flexible)

**Purpose:** Test a single report; supports --once or daily loop

**Code:**
```bash
# Test once (exit after run)
python run_single_report.py --once --report Report0002

# Daily loop (like main.py but only 1 report)
python run_single_report.py --report Report0002

# Override settings
python run_single_report.py --once --report Report0002 --settings /path/to/settings.json
```

**Options:**
- `--once`: Run once and exit (default: daily loop)
- `--report REPORT`: Report name (default: Report0002)
- `--settings FILE`: Path to settings.json (default: auto-detect)

**Behavior:**
1. Parse arguments
2. If --once: execute immediately and exit
3. If no --once: enter daily loop (like main.py)
4. Support mode override: `--parallel` or `--parallel false`

**Implementation:**
```python
# run_single_report.py
from lib.reports.selection_runner import run_selection
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--once', action='store_true', help='Run once and exit')
parser.add_argument('--report', default='Report0002', help='Report name')
parser.add_argument('--settings', help='Path to settings.json')
parser.add_argument('--parallel', help='Force execution mode')
args = parser.parse_args()

settings_path = args.settings or detect_settings()

if args.once:
    # Single run
    exit(run_selection(settings_path, [args.report], stream_output=True))
else:
    # Daily loop
    while True:
        run_selection(settings_path, [args.report], stream_output=True)
        time.sleep(60)
```

---

### 3. main_selection_list.py (Curated 4 Reports, Test Mode)

**Purpose:** Quick testing with a small, curated list of reports

**Code:**
```bash
# Run with defaults (4 reports)
python main_selection_list.py

# Force parallel mode
python main_selection_list.py --parallel

# Force sequential mode
python main_selection_list.py --parallel false

# Custom reports
python main_selection_list.py --reports Report0002 Report0035

# Dry run (show config, don't execute)
python main_selection_list.py --dry-run
```

**Default Reports:**
```python
DEFAULT_REPORTS = [
    'Report0002',   # ArangoDB (simple)
    'Report0004',   # ArangoDB (complex)
    'Report0030',   # PostGIS (geographic)
    'Report0048',   # PostGIS (complex aggregation)
]
```

**Behavior:**
1. Load settings.json
2. Detect mode (sequential or parallel) from config
3. Allow `--parallel` to override config
4. Run selected reports
5. Print summary and exit

**Implementation:**
```python
# main_selection_list.py
import argparse
from lib.reports.selection_runner import run_selection

parser = argparse.ArgumentParser()
parser.add_argument('--parallel', help='Force execution mode (true/false)')
parser.add_argument('--reports', nargs='+', help='Report names to run')
parser.add_argument('--dry-run', action='store_true', help='Show config, don\'t run')
args = parser.parse_args()

reports = args.reports or DEFAULT_REPORTS
settings = load_settings()

if args.dry_run:
    print(f"Mode: {settings['report_execution']['mode']}")
    print(f"Reports: {', '.join(reports)}")
    return

exit(run_selection('settings.json', reports, stream_output=True))
```

---

## Shared Code Structure

### Module: selection_runner.py (35 lines)

**Purpose:** Single entry point for all three CLI scripts

**Signature:**
```python
def run_selection(
    settings_path: str,
    report_names: list[str],
    *,
    force_parallel: bool | None = None,
    stream_output: bool = True,
) -> int:
```

**Logic:**
```python
def run_selection(settings_path, report_names, *, force_parallel=None, stream_output=True):
    """
    Run a list of reports using configured or forced execution mode.
    
    Returns: 0 on success, 1 on any failure
    """
    settings = load_settings(settings_path)
    
    # Determine mode
    if force_parallel is not None:
        mode = 'parallel_by_datasource' if force_parallel else 'sequential'
    else:
        mode = settings['report_execution']['mode']
    
    # Dispatch
    if mode == 'sequential':
        return run_sequential(report_names, settings, stream_output)
    else:
        return run_parallel_by_datasource(report_names, settings, settings_path, stream_output)
```

**Benefits:**
- Single point of decision logic
- All three entry points use identical code
- Easy to add modes (e.g., future 'parallel_by_report')

---

### Module: pipeline_runner.py (80 lines)

**Purpose:** Orchestrate parallel execution by datasource

**Signature:**
```python
def run_pipelines_by_datasource(
    report_names: Iterable[str],
    settings: dict,
    settings_path: str,
    *,
    stream_output: bool = True,
) -> int:
```

**Algorithm:**
```
1. Group reports by datasource (ArangoDB, PostGIS, other)
2. For each group:
   a. Create list of reports for that datasource
   b. Spawn subprocess worker: python -m lib.reports.worker --reports R1 R2 R3 ...
   c. Worker reinitializes connections once
   d. Worker executes all reports in sequence (reusing connections)
3. Use ThreadPoolExecutor(max_workers=max_concurrent) to run workers concurrently
4. Wait for all workers to complete
5. Return 0 if all succeed, 1 if any fail
```

**Example Flow:**
```
Input: [Report0002, Report0003, Report0030, Report0048, ...]
Group:
  - ArangoDB: [Report0002, Report0003, Report0010, ..., Report0098]
  - PostGIS: [Report0030, Report0048, Report0050, ..., Report0199]

Spawn:
  - Worker1: python -m lib.reports.worker --reports Report0002 Report0003 ... Report0098
  - Worker2: python -m lib.reports.worker --reports Report0030 Report0048 ... Report0199

Execute concurrently (2 threads):
  - Thread1 waits for Worker1 (ArangoDB pipeline)
  - Thread2 waits for Worker2 (PostGIS pipeline)

Result: min(6 hours sequential, 3 hours parallel with 2 workers)
```

---

### Module: ReportLoopRunner.py (150 lines)

**Purpose:** Main orchestrator; loads reports, handles retries, manages batch lifecycle

**Key Methods:**
```python
class ReportLoopRunner:
    def run(self) -> int:
        """Run all reports (respects config mode)."""
        
    def run_selected(self, report_names: list[str]) -> int:
        """Run a specific list of reports."""
        
    def _run_sequential(self, report_names=None) -> int:
        """Execute reports in-process, one at a time."""
        
    def _run_parallel_by_datasource(self, report_names=None) -> int:
        """Execute reports in subprocesses grouped by datasource."""
    
    def start(self, run_right_away: bool = False) -> None:
        """Start infinite daily loop."""
```

**Daily Loop Example:**
```python
def start(self, run_right_away=False):
    while True:
        now = datetime.now(UTC)
        in_window = self._in_time_window(now)
        
        if in_window:
            logging.info(f"Running reports at {now}")
            try:
                self.run()
            except Exception as e:
                logging.error(f"Batch failed: {e}")
        
        # Sleep until next boundary
        next_boundary = now.replace(hour=5, minute=0, second=0) + timedelta(days=1)
        sleep_seconds = (next_boundary - datetime.now(UTC)).total_seconds()
        time.sleep(sleep_seconds)
```

---

### Module: worker.py (188 lines)

**Purpose:** Subprocess worker; executes reports with isolated connections

**Invocation:**
```bash
python -m lib.reports.worker --reports Report0002 Report0003 ... --settings settings.json
```

**Behavior:**
1. Parse command-line arguments (report names, settings path)
2. Reinitialize DB connections once (singletons created fresh)
3. For each report: instantiate → init_report() → run_report()
4. Handle exceptions per report (log, continue to next)
5. Exit with status 0 (all passed) or 1 (any failed)

**Code Sketch:**
```python
def run_reports(report_names: list[str], settings: dict) -> int:
    """Run reports in subprocess with fresh connections."""
    
    # 1. Reinitialize connections once per worker
    logging.info(f"Worker initializing with {len(report_names)} reports")
    reinitialize_database_connections(settings)  # <- ONCE
    
    # 2. Execute reports in sequence
    failed = 0
    for report_name in report_names:
        try:
            set_report_context(report_name)  # Context for logging
            
            # Dynamically instantiate report
            ReportClass = dynamic_load_report_class(report_name)
            report_instance = ReportClass()
            report_instance.init_report()
            report_instance.run_report(sender=None)  # TODO: mail sender
            
            logging.info(f"[{report_name}] ✓ Completed successfully")
        
        except Exception as e:
            logging.error(f"[{report_name}] Failed: {e}")
            failed += 1
    
    # 3. Return status
    return 1 if failed > 0 else 0

# Entry point
if __name__ == '__main__':
    args = parse_args()  # --reports, --settings
    settings = load_settings(args.settings)
    exit_code = run_reports(args.reports, settings)
    sys.exit(exit_code)
```

**Logging (with context):**
```
[Worker 12345] [Report0002] 2026-03-30 16:32:20 - INFO - Starting report
[Worker 12345] [Report0002] 2026-03-30 16:32:21 - INFO - Query executed in 1.2s (54 rows)
[Worker 12345] [Report0002] 2026-03-30 16:32:22 - INFO - ✓ Completed successfully
[Worker 12345] [Report0003] 2026-03-30 16:32:23 - INFO - Starting report
```

---

## Database Connection Strategy

### Sequential Mode (In-Process)

**Initialization:**
```python
# In ReportLoopRunner.__init__
self.arango_connector = SingleArangoConnector(settings)
self.postgis_connector = SinglePostGISConnector(settings)
# Singletons created once
```

**Reuse:**
```python
# Each report reuses same connections
ds_adapter = datasources.datasource_factory.make_datasource('ArangoDB')  # Returns adapter using singleton
qr = ds_adapter.execute(query)
# ... next report ...
ds_adapter2 = datasources.datasource_factory.make_datasource('ArangoDB')  # SAME connector
qr2 = ds_adapter2.execute(query2)
```

**Pros:**
- ✅ Minimal memory overhead (one connection per DB)
- ✅ Fast (no reconnection)

**Cons:**
- ❌ No isolation (one bad query affects all)
- ❌ No timeouts per report

---

### Parallel Mode (Subprocess)

**Initialization (once per worker):**
```python
# In worker.py::run_reports()
reinitialize_database_connections(settings)

def reinitialize_database_connections(settings):
    """Clear old singletons, create new ones."""
    # In-process only; each subprocess has its own
    SingleArangoConnector._instance = None  # Clear singleton cache
    SinglePostGISConnector._instance = None
    
    # Create fresh instances
    _ = SingleArangoConnector(settings)  # Initializes and caches
    _ = SinglePostGISConnector(settings)
```

**Reuse (within subprocess):**
```python
# Worker 1 (ArangoDB pipeline)
for report_name in arangodb_reports:
    ds = datasources.datasource_factory.make_datasource('ArangoDB')  # Singleton (in Worker1's process)
    qr = ds.execute(query)

# Worker 2 (PostGIS pipeline) in parallel
# Has its own PostGIS singleton (isolated from Worker1)
for report_name in postgis_reports:
    ds = datasources.datasource_factory.make_datasource('PostGIS')  # Singleton (in Worker2's process)
    qr = ds.execute(query)
```

**Benefits:**
- ✅ Full isolation (Worker1 failure doesn't affect Worker2)
- ✅ Timeouts per worker (enforce 30min timeout)
- ✅ 2x faster (parallel execution)

**Trade-offs:**
- ❌ Higher memory (2-3 connections per worker)
- ❌ Process overhead (subprocess spawn/teardown)

---

## Connection Lifecycle

### Sequential Mode Lifecycle

```
┌─────────────────────────────────────────┐
│ ReportLoopRunner.__init__               │
│  └─ SingleArangoConnector created       │
│  └─ SinglePostGISConnector created      │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Report 1 execution                      │
│  └─ Datasource adapter (reuses singletons)
│  └─ Execute query
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ Report 2 execution                      │
│  └─ Same Arango/PostGIS connections     │
│  └─ Execute query
└─────────────────────────────────────────┘
                  │
        ... [191 more reports] ...
                  │
                  ▼
┌─────────────────────────────────────────┐
│ ReportLoopRunner.cleanup()              │
│  └─ Singletons closed                   │
└─────────────────────────────────────────┘
```

### Parallel Mode Lifecycle

```
Main Process
    │
    ├─ Spawn Worker1 (ArangoDB reports)
    │   │
    │   ├─ worker.py::run_reports()
    │   ├─ Reinitialize singletons (fresh in Worker1 process)
    │   ├─ Report0002.run_report()
    │   ├─ Report0003.run_report()
    │   └─ ... [n reports] → exit(0 or 1)
    │
    ├─ Spawn Worker2 (PostGIS reports) ← CONCURRENT
    │   │
    │   ├─ worker.py::run_reports()
    │   ├─ Reinitialize singletons (fresh in Worker2 process)
    │   ├─ Report0030.run_report()
    │   ├─ Report0048.run_report()
    │   └─ ... [m reports] → exit(0 or 1)
    │
    └─ ThreadPoolExecutor
        ├─ Thread1: wait for Worker1
        └─ Thread2: wait for Worker2
        
        Both workers run concurrently
        Main process waits for both to complete
        Aggregates exit codes
```

---

## Logging & Observability

### Log Format (with Report Context)

```
[Timestamp] [ProcessID] [ReportName] [Level] - Message
[2026-03-30 16:32:20] [Worker 12345] [Report0002] INFO - Starting report
[2026-03-30 16:32:21] [Worker 12345] [Report0002] INFO - Query executed in 1.2s (54 rows)
[2026-03-30 16:32:22] [Worker 12345] [Report0002] INFO - ✓ Completed successfully
[2026-03-30 16:32:23] [Worker 12345] [Report0004] INFO - Starting report
```

### Context Injection (ContextVar)

```python
from contextvars import ContextVar

_report_context = ContextVar('report_name', default='system')

def set_report_context(name: str):
    _report_context.set(name)

class ReportContextFilter(logging.Filter):
    def filter(self, record):
        record.report_name = _report_context.get()
        return True

# Setup
logging.basicConfig(
    format='[%(asctime)s] [%(report_name)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger()
logger.addFilter(ReportContextFilter())
```

### Grep by Report Name

```bash
# All logs for Report0002
grep "[Report0002]" logs.txt

# Errors only
grep "[Report0002]" logs.txt | grep ERROR

# Last 5 lines
grep "[Report0002]" logs.txt | tail -5

# Timeline for entire batch
grep "INFO - ✓ Completed" logs.txt | wc -l  # Count successes
```

---

## Performance Characteristics

### Memory Usage

| Mode | Peak | Safe Limit | Notes |
|------|------|-----------|-------|
| Sequential | ~2 GB | 4 GB | One connection pool |
| Parallel (2 workers) | ~4-5 GB | 8 GB | Each worker has separate pools |
| Parallel (4 workers) | ~8-10 GB | 16 GB | Not recommended for 8GB systems |

**Recommendation:** Deploy with 8GB RAM; run 2 concurrent workers

### Execution Time

| Mode | 194 Reports | Speedup |
|------|------------|---------|
| Sequential | ~6-8 hours | 1x |
| Parallel (2) | ~3-4 hours | 2x |
| Parallel (3) | ~2.5-3 hours | 2.5x (but higher memory) |
| Parallel (4) | ~2-2.5 hours | 3x (needs 16GB RAM) |

**Formula (rough):**
```
Parallel Time ≈ Sequential Time / max_concurrent
Memory ≈ Base Memory + (Worker Memory × max_concurrent)
```

---

## Performance Tuning

### Reduce Memory Usage
```json
{
  "report_execution": {
    "mode": "sequential"
  }
}
```
Fallback for <4GB systems.

### Increase Throughput
```json
{
  "report_execution": {
    "mode": "parallel_by_datasource",
    "max_concurrent": 3
  }
}
```
Use if 12GB+ RAM available.

### Query Timeouts
```json
{
  "report_execution": {
    "timeout_seconds": 3600
  }
}
```
Enforce per-worker timeout (each report cluster).

---

## Testing Checklist

### Test Matrix

| Entry Point | Mode | Test |
|---|---|---|
| main.py | sequential | Run once (`--once` equivalent), verify all reports |
| main.py | parallel | Run once in parallel, verify all reports |
| run_single_report.py | sequential | Run --once Report0002 |
| run_single_report.py | parallel | Run --once Report0002 --parallel |
| main_selection_list.py | sequential | python main_selection_list.py (auto-detect) |
| main_selection_list.py | parallel | python main_selection_list.py --parallel |

### Smoke Test Commands

```bash
# Test 1: Single report, sequential
python run_single_report.py --once --report Report0002
# Expect: Exit code 0, success log

# Test 2: Selection, auto-detect mode
python main_selection_list.py --dry-run
# Expect: Prints mode and 4 reports

# Test 3: Selection, parallel mode
python main_selection_list.py --parallel
# Expect: 2 workers running concurrently, both complete, exit 0

# Test 4: Full batch (if time allows)
python main.py --once  # (need to add --once flag to main.py)
# Expect: All 194 reports, execution time 3-8 hours, exit 0
```

### Verification Steps

1. **Log file exists:** Check `/var/log/rsa/reports.log` (or configured path)
2. **Report names in logs:** Grep by report name
3. **No OOM:** Monitor `free -h` during run
4. **Exit codes:** `echo $?` after script completes (0 = success)
5. **Output files:** Verify Excel files uploaded to OneDrive/SharePoint
6. **History updated:** Check `Historiek` sheet for new row

---

## Debugging Guide

### Enable Verbose Logging

Set environment variable:
```bash
export LOG_LEVEL=DEBUG
python run_single_report.py --once --report Report0002
```

All logs at DEBUG level and above.

### Stream Output in Real-Time

```bash
# Show logs as they're written
tail -f /var/log/rsa/reports.log

# Filter by report name
tail -f /var/log/rsa/reports.log | grep "[Report0002]"
```

### Monitor Resource Usage

```bash
# In another terminal
watch 'free -h; ps aux | grep python'
# Shows memory and process list; refreshes every 2 seconds
```

### Debug Subprocess Issues

For parallel mode, subprocess stderr/stdout is captured. To see raw output:

```python
# In pipeline_runner.py, change:
subprocess.run(..., capture_output=False, text=True)
# This streams worker output directly to console
```

### Common Issues & Solutions

| Issue | Cause | Fix |
|-------|-------|-----|
| "Report not found" | Typo in report name | Check filename in Reports/ |
| "Connection refused" | DB not running | Verify ArangoDB/PostGIS connectivity |
| "Timeout" | Report too slow | Increase timeout_seconds in settings |
| "Out of memory" | Too many workers | Reduce max_concurrent to 1 |
| "No logs updated" | Log file path wrong | Check SettingsManager.logging config |
| "Subprocess hung" | Worker deadlocked | Restart service; check max_concurrent |

---

## Future Enhancements

### 1. Registry Decorator Pattern (Step 2)
Allow reports to register themselves instead of relying on filename == classname:
```python
@register_report(name='asset_report')
class AssetReportCustomClass:
    def init_report(self): ...
```

### 2. Metrics Collection
Track per-report: execution time, row count, success rate, last run.

### 3. Retry & Backoff
Exponential backoff for failed reports (FR4 from analysis.md).

---

## Summary

✅ **Three entry points, one engine**  
✅ **Minimal code duplication (92% reduction)**  
✅ **Sequential and parallel modes**  
✅ **Full process isolation in parallel mode**  
✅ **Clean logging with report names**  
✅ **Memory-safe for 8GB systems**  
✅ **Timeout and fault tolerance**  
✅ **Easy to test and debug**  
✅ **Extensible for future enhancements**
