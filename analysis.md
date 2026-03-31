# Analysis — Functional Requirements, Criteria & Data Contracts

## Contents

- [Problem Statement](#problem-statement)
- [Functional Requirements (FR)](#functional-requirements-fr)
- [Non-Functional Requirements (NFR)](#non-functional-requirements-nfr)
- [Acceptance Criteria (Testing & Validation)](#acceptance-criteria-testing--validation)
- [Rollout Plan (Phases)](#rollout-plan-phases)
- [Configuration Schema](#configuration-schema)
- [Traceability](#traceability)
- [Edge Cases & Open Questions](#edge-cases--open-questions)

## Problem Statement

The report service needs a **refactored, extensible architecture** that:
1. Supports multiple data sources (ArangoDB, PostGIS) independently
2. Outputs to Excel with OneDrive/SharePoint upload
3. Never fails silently — retry logic with exponential backoff
4. Provides observable, testable adapters for datasources and outputs
5. Maintains backwards compatibility with ~194 existing reports

---

## Functional Requirements (FR)

### FR1: Excel Output Backend
**Requirement:** The service must generate and upload Excel reports instead of Google Sheets.

**Details:**
- Report is rendered locally as `.xlsx` file (using openpyxl or xlsxwriter)
- File is uploaded to OneDrive/SharePoint using configured credentials or agent-based sync
- Output adapters are extensible (interface/abstract class pattern)
- Same `OutputWriteContext` contract remains; `DQReport.run()` calls `out.write_report(ctx, qr, ...)` unchanged

**Acceptance Criteria:**
- [ ] At least one report successfully outputs to Excel and uploads to configured target
- [ ] Multiple reports can be queued and uploaded concurrently (if applicable)

---

### FR2: Datasource Abstraction
**Requirement:** All datasources (ArangoDB, PostGIS) must implement a unified adapter interface.

**Details:**
- Each adapter implements `Datasource` protocol: `test_connection()` and `execute(query: str) -> QueryResult`
- Adapters are created by `datasources.datasource_factory.make_datasource(datasource_name)`
- Adapters must work independently (swappable in config)

**Acceptance Criteria:**
- [ ] ArangoDB adapter returns `QueryResult` with all mandatory fields
- [ ] PostGIS adapter returns `QueryResult` with all mandatory fields
- [ ] Connection errors raise descriptive exceptions

---

### FR3: QueryResult Data Contract
**Requirement:** All datasources return a unified `QueryResult` object.

**Data Contract:**
```python
@dataclass(frozen=True)
class QueryResult:
    keys: list[str]                          # Column names (mandatory, never empty)
    rows: list[Sequence[Any] | dict]         # Rows as dicts (ArangoDB) or tuples (PostGIS)
    last_data_update: str | None = None      # ISO timestamp of last DB sync
    query_time_seconds: float | None = None  # Query execution time

    def to_rows_list(self) -> list[list]:
        """Convert rows to list[list], normalizing dicts and tuples."""
        
    def iter_rows(self):
        """Memory-efficient iterator for large result sets."""
```

**Responsibility Matrix:**

| Responsibility | Who | How |
|---|---|---|
| Populate `rows` | Datasource adapter | Execute query, normalize results |
| Populate `keys` | Datasource adapter | Extract from cursor.description (SQL) or rows[0].keys() (ArangoDB) |
| Populate `query_time_seconds` | Datasource adapter | Measure execution time |
| Populate `last_data_update` | Datasource adapter | ArangoDB: from `params` collection (finished_at); PostGIS: from connector metadata |
| Normalize to list[list] | QueryResult helper (to_rows_list) | Iterate and convert dicts → lists by keys order |
| Stream rows efficiently | QueryResult helper (iter_rows) | Generator for memory-efficient writes |

**Acceptance Criteria:**
- [ ] All datasources MUST populate `keys` (never empty after execute)
- [ ] `keys` order matches actual data order in rows
- [ ] `to_rows_list()` produces identical output regardless of row format (dict vs tuple)
- [ ] `iter_rows()` works for result sets >10K rows without OOM

---

### FR4: Retry Logic & Fault Handling
**Requirement:** Broken reports must retry automatically; never stall the batch.

**Details:**
- Each report gets up to N retries (configurable, default 3)
- Exponential backoff: 2^attempt seconds between retries (2s, 4s, 8s, ...)
- If all retries fail:
  - Report is logged as failed
  - Error logs uploaded to central storage (S3 or configurable)
  - Email notification sent
  - **Batch continues** to next report (isolation per report)
- Per-report failures don't stop the overall batch

**Configuration Example:**
```json
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_base_seconds": 2,
    "remote_upload_target": "s3://logs-bucket/errors"
  }
}
```

**Acceptance Criteria:**
- [ ] Simulate report failure; verify 3 retries executed
- [ ] After all retries exhaust, error logs are uploaded
- [ ] Next report in batch continues running
- [ ] Email notification includes error summary and retry count

---

### FR5: Mail Notifications
**Requirement:** Mail notifications are report-driven; recipients and frequency come from each report definition.

**Details:**
- Email sending is triggered by report metadata (addresses + frequency) stored in report files.
- There is no central/configurable mailing list in `settings.json`.
- Transport can still use existing mail infrastructure (`MailSender` / SMTP wiring).
- Frequency logic is evaluated per report (e.g., daily/weekly cadence as defined in the report).
- Report mails can include report-specific summary data (row counts, timestamps, failures if relevant).

**Acceptance Criteria:**
- [ ] For a report with configured recipients in its file, mail is sent to those recipients only.
- [ ] For a report with no recipients configured, no mail is sent.
- [ ] Frequency in the report definition is respected (no extra sends outside cadence).

---

### FR6: History & Summary Sheets
**Requirement:** Track run history and maintain summary metadata.

**Details:**
- History sheet (`Historiek`): one row per run, columns: `now_utc`, `last_data_update` per datasource, row count per report
- Summary sheet (`Overzicht`): current snapshot of all reports (last run timestamp, row count, status)
- For ArangoDB: `last_data_update` derived from `params` collection (`finished_at`)
- For PostGIS: `last_data_update` derived from `SinglePostGISConnector.get_params()` attribute `last_update_utc_assets`

**Acceptance Criteria:**
- [ ] `Historiek` sheet updated after each batch run
- [ ] `Overzicht` sheet current and accurate
- [ ] `last_data_update` correctly sourced per datasource

---

## Non-Functional Requirements (NFR)

### NFR1: Reliability
**Requirement:** System must handle errors gracefully without data loss or silent failures.

- All external operations (DB queries, uploads, emails) must have error handlers
- Connection pooling must auto-recover on transient failures
- No report failure cascades to others
- Logs must capture error context (query, datasource, retry count)

---

### NFR2: Observability
**Requirement:** All significant operations must be logged with full context.

- Log lines include: timestamp, report name, log level, message
- Report context injected via `ContextVar` + custom filter (not manual threading)
- Failed reports logged with full error traceback + retry count
- Upload operations (logs, files) logged with result status
- Example:
  ```
  [2026-03-30 16:32:20] [Report0002] INFO - Starting report
  [2026-03-30 16:32:25] [Report0002] INFO - ✓ Completed successfully (54 rows, 5.2s)
  [2026-03-30 16:32:26] [Report0004] ERROR - Connection failed (retry 2/3)
  ```

---

### NFR3: Testability
**Requirement:** Adapters must be mockable and testable in isolation.

- Datasource protocol (base class / Protocol) allows mock implementations
- Unit tests for adapters with mocked DB connections
- Integration tests can swap real datasources for test doubles
- Fixtures for QueryResult and OutputWriteContext provided

---

### NFR4: Extensibility
**Requirement:** New adapters must be add-able without modifying core.

- OOP design with Protocol / ABC
- Dependency injection (factories)
- Configuration-driven selection (`settings.json` → datasource type)
- New adapters added via factory registration (no core code changes)

---

### NFR5: Performance
**Requirement:** Large result sets must not cause OOM or timeout.

- Use derived edge collections in ArangoDB (e.g., `voedt_relaties` instead of `assetrelaties`)
- Output adapters use `iter_rows()` for >1000-row result sets
- Connection pooling to limit resource exhaustion
- Query timeouts configured per datasource

---

## Acceptance Criteria (Testing & Validation)

### AC1: QueryResult Contract
```gherkin
Given a datasource adapter (ArangoDB or PostGIS)
When execute(query) is called
Then QueryResult is returned with:
  - keys: non-empty list of strings
  - rows: non-empty list of dicts or tuples
  - query_time_seconds: positive float
  - last_data_update: ISO timestamp or None
And to_rows_list() produces list[list] matching keys order
And iter_rows() yields same data without OOM on large sets
```

### AC2: Retry Logic
```gherkin
Given a report that fails on execute
When run_report() is called
Then up to max_retries attempts are made
And exponential backoff is observed between retries
And after all retries fail:
  - Error log is uploaded to remote target
  - Email notification is sent
  - Batch continues to next report
```

### AC3: Datasource Independence
```gherkin
Given two reports (one ArangoDB, one PostGIS)
When both are run in same batch
Then each datasource is queried correctly
And neither failure affects the other
```

### AC4: Excel Output
```gherkin
Given a report with QueryResult
When Excel output adapter writes
Then local .xlsx file is created
And file contains all rows/columns from QueryResult
And file is successfully uploaded to OneDrive/SharePoint
```

### AC5: History & Summary
```gherkin
Given a batch run with N reports
When batch completes
Then Historiek sheet has one new row with:
  - current UTC timestamp
  - last_data_update per datasource
  - row count per report
And Overzicht sheet is updated
```

---

## Rollout Plan (Phases)

### Phase 0: Tests & Infrastructure Preparation
**Duration:** Week 1  
**Goals:** Foundation for safe refactoring

- [ ] Add unit tests for QueryResult contract (to_rows_list, iter_rows)
- [ ] Add unit tests for datasource adapters (with mocked DB)
- [ ] Add integration tests for output adapters (write to temp file)
- [ ] Verify config schema and credential placement
- [ ] Set up S3 or alternative log upload target

**Deliverable:** Test infrastructure, 80%+ coverage on adapters

---

### Phase 1: Adapter & Output Scaffolding
**Duration:** Week 2-3  
**Goals:** Core adapters working with QueryResult contract

- [ ] Implement `QueryResult` dataclass in `datasources/base.py`
- [ ] Implement `ArangoDatasource` adapter (execute, keys population, last_data_update)
- [ ] Implement `PostGISDatasource` adapter (execute, keys population, last_data_update)
- [ ] Implement `ExcelOutput` adapter (write .xlsx, upload to OneDrive/SharePoint)
- [ ] Update `datasources.datasource_factory.make_datasource()` to return new adapters
- [ ] Run existing reports with new adapters; verify outputs match baseline

**Deliverable:** One report runs successfully with Excel output (e.g., Report0002)

---

### Phase 2: Retry & Error Handling
**Duration:** Week 3-4  
**Goals:** Resilient batch execution

- [ ] Implement retry logic with exponential backoff in `ReportLoopRunner`
- [ ] Implement error log collection and upload to remote target
- [ ] Implement email notification on batch completion
- [ ] Simulate report failures; verify retries and log uploads
- [ ] Test batch isolation (one failure doesn't stop others)

**Deliverable:** Batch handles failures gracefully; logs uploaded, emails sent

---

### Phase 3: Monitoring & Documentation
**Duration:** Week 4-5  
**Goals:** Production readiness

- [ ] Finalize logging with context injection (ContextVar, ReportContextFilter)
- [ ] Verify performance metrics (time per report, memory usage)
- [ ] Update History (`Historiek`) and Summary (`Overzicht`) sheets post-run
- [ ] Write deployment runbook (systemd service, cron, Docker if applicable)
- [ ] Finalize `implementation_details.md` and `architecture.md` docs

**Deliverable:** Full batch run (194 reports) with monitoring, <5 GB RAM, 3-4 hours (parallel)

---

## Configuration Schema

### settings.json Structure
```json
{
  "databases": {
    "arango": {
      "host": "localhost",
      "port": 8529,
      "user": "root",
      "password": "secret",
      "dbname": "asset_db"
    },
    "postgis": {
      "host": "localhost",
      "port": 5432,
      "user": "gis_user",
      "password": "secret",
      "dbname": "gis_db"
    }
  },
  "output": {
    "type": "excel",
    "excel": {
      "upload_target": "onedrive://path/to/reports",
      "credentials": "~/.credentials/onedrive.json"
    }
  },
  "report_execution": {
    "mode": "parallel_by_datasource",
    "max_concurrent": 2,
    "timeout_seconds": 1800
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_base_seconds": 2,
    "remote_upload_target": "s3://logs-bucket/errors"
  },
  "time_window": {
    "start_hour": 5,
    "end_hour": 23
  }
}
```

---

## Traceability

| FR | Component(s) | Test Coverage |
|---|---|---|
| FR1 (Excel Output) | `outputs/excel.py`, `ExcelWriter` | Integration test: write + upload |
| FR2 (Datasource Abstraction) | `datasources/arango.py`, `datasources/postgis.py`, `datasources/datasource_factory.py` | Unit tests: execute, keys population |
| FR3 (QueryResult) | `datasources/base.py` | Unit tests: to_rows_list, iter_rows |
| FR4 (Retry Logic) | `lib/reports/ReportLoopRunner.py` | Simulation: failure + 3 retries |
| FR5 (Mail Notifications) | `Reports/`, `lib/mail/MailSender.py` | Mock SMTP: verify report-defined recipients/frequency |
| FR6 (History & Summary) | `outputs/summary_stager.py` | Verify sheet rows updated |

---

## Edge Cases & Open Questions

### Edge Case: ArangoDB params.finished_at Missing
**Scenario:** A report runs but `params.finished_at` is not set.  
**Handling:** `last_data_update` set to `None`; report still executes but summary shows "unknown"  
**Resolution:** Document in implementation_details.md; alert if missing (future NFR)

### Edge Case: PostGIS Transaction Abort
**Scenario:** `current transaction is aborted` error mid-query.  
**Handling:** Auto-rollback and retry (implemented in `SinglePostGISConnector`)  
**Resolution:** Verify in integration tests

### Edge Case: Excel File Locked
**Scenario:** Upload target file is open in Excel on OneDrive.  
**Handling:** Retry with exponential backoff; if all retries fail, log error and continue  
**Resolution:** Document in troubleshooting guide

### Question: Multi-Language Support?
**Current:** All logs and emails in English  
**Future:** Internationalization (if needed)

### Question: Backwards Compat with Neo4j?
**Current:** Code compiles but not executed  
**Plan:** Keep imports; mark deprecated; phase out in 6 months (v2.0)




