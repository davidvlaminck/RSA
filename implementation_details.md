# Implementation Details — Report Types, Adapters & Development

## Contents

- [Report Architecture Overview](#report-architecture-overview)
- [Report Types](#report-types)
- [Report API Contract](#report-api-contract)
- [DQReport Execution Detail](#dqreport-execution-detail)
- [Datasource Adapters](#datasource-adapters)
- [Output Adapters](#output-adapters)
- [QueryResult & Conversion](#queryresult--conversion)
- [Configuration & Settings](#configuration--settings)
- [Logging Strategy](#logging-strategy)
- [Testing & Mocking](#testing--mocking)
- [Creating a New Report](#creating-a-new-report)
- [Backwards Compatibility](#backwards-compatibility)

## Report Architecture Overview

Reports in this system combine three layers:

1. **Extraction**: Datasource adapter executes query → returns `QueryResult`
2. **Processing**: Report class transforms and prepares output
3. **Output**: Output adapter writes to Excel, handles upload

```
┌─────────────────────────────────────────┐
│         Report Class                    │
│  (init_report, run_report)              │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┬────────────┐
    ▼                 ▼            ▼
Datasource        Output        Config
Adapter           Adapter
```

---

## Report Types

### 1. DQReport (Modern, Recommended)
**Location:** `lib/reports/DQReport.py`  
**Pattern:** Clean separation of concerns; uses factories for adapters.

**Lifecycle:**
```python
class Report0002:
    def init_report(self):
        self.report = DQReport(
            name='report_0002',
            title='Asset Connection Report',
            spreadsheet_id='output_sheet_id',
            datasource='ArangoDB',
            output='excel'
        )
        self.report.result_query = """
            FOR v IN assets
            RETURN { name: v.name, type: v.type }
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
```

**Execution Flow:**
1. `DQReport.run_report(sender)` called
2. Datasource adapter created via `factories.make_datasource()`
3. `adapter.test_connection()` → raises if unreachable
4. `qr = adapter.execute(result_query)` → returns `QueryResult`
5. Output adapter created via `factories.make_output()`
6. `output.write_report(ctx, qr, ...)` → writes to Excel
7. History (`Historiek`) and summary (`Overzicht`) updated
8. Mail sent if configured

**Key Features:**
- ✅ Extensible datasource/output via factories
- ✅ Automatic key population (even if datasource returns empty keys)
- ✅ Persistent column support (preserve user comments)
- ✅ History tracking
- ✅ Email notifications

**When to Use:** All new reports; most production reports

---

### 2. LegacyReport (Deprecated, PostGIS-focused)
**Location:** Scattered; older reports use this pattern  
**Pattern:** Direct connector access; query logic embedded in class

**Lifecycle:**
```python
class Report0030:
    def init_report(self):
        self.connector = SinglePostGISConnector.get_connector()
        self.result_keys = ['id', 'name', 'geometry']

    def run_report(self, sender):
        cursor = self.connector.execute("SELECT * FROM assets")
        rows = cursor.fetchall()
        # Manual row processing, sheet writing, etc.
```

**Issues:**
- ❌ No `QueryResult` contract; keys and rows managed manually
- ❌ Sheet writing logic embedded (code duplication)
- ❌ Harder to test (direct connector coupling)

**Migration Path:** Wrap in `DQReport`; move query to `result_query` attribute

---

### 3. LegacyHistoryReport (Deprecated)
**Pattern:** Like `LegacyReport` but maintains rolling history.

**Features:**
- Creates new sheet per run (dated: `dd/mm/YYYY`)
- Maintains `Historiek` and `Overzicht` summary
- Persistent column support

**Status:** Still used for some reports; consider migration to `DQReport`

---

### 4. KladRapport (Development/Test)
**Location:** Root directory; `KladRapport.py`  
**Purpose:** Ad-hoc testing during development

**Usage:**
```python
# Run a test report locally
python KladRapport.py

# Initializes connectors manually, instantiates DQReport, runs once
```

---

### 5. OTLCursorPool (Singleton Accessor)
**Location:** `lib/connectors/OTLCursorPool.py`  
**Purpose:** Manages read-only SQLite cursors for OTL database

**Usage:**
```python
from lib.connectors.OTLCursorPool import OTLCursorPool

cursor = OTLCursorPool().get_cursor()
cursor.execute("SELECT * FROM assets")
rows = cursor.fetchall()
```

**Pattern:** Singleton; lazy-loads most recent OTL SQLite database

---

## Report API Contract

Every report **must** implement this minimal interface:

### init_report()
**Purpose:** Initialize report metadata and queries; called once before `run_report()`.

**Signature:**
```python
def init_report(self):
    """Initialize report. Must populate self.report attribute."""
```

**Responsibilities:**
- Create report instance (typically `DQReport`)
- Load or define `result_query` (AQL for ArangoDB, SQL for PostGIS)
- Set output destination (sheet ID, file path, etc.)
- Configure retry, mail, and other options

**Example:**
```python
def init_report(self):
    self.report = DQReport(
        name='asset_connections',
        title='Asset Connection Report',
        datasource='ArangoDB',
        output='excel'
    )
    self.report.result_query = """
        FOR v IN assets
        LIMIT 1000
        RETURN { id: v._id, name: v.name }
    """
```

---

### run_report(sender)
**Purpose:** Execute report; called by orchestrator per batch run.

**Signature:**
```python
def run_report(self, sender):
    """Run report. sender is an email MailSender instance."""
```

**Responsibilities:**
- Call `self.report.run_report(sender=sender)`
- Catch and log exceptions (orchestrator handles isolation)
- Don't directly manipulate sheets (output adapters do that)

**Example:**
```python
def run_report(self, sender):
    try:
        self.report.run_report(sender=sender)
    except Exception as e:
        logging.error(f"Report failed: {e}")
        raise  # Let orchestrator handle retry
```

---

## DQReport Execution Detail

### Code Walkthrough

```python
class DQReport:
    def __init__(self, name, title, datasource, output, **kwargs):
        self.name = name
        self.title = title
        self.datasource = datasource
        self.output = output
        self.result_query = None
        # ... more init

    def run_report(self, sender=None):
        """Main execution method."""
        try:
            # 1. Create adapters
            ds_adapter = factories.make_datasource(self.datasource)
            out_adapter = factories.make_output(self.output)
            
            # 2. Test connection
            ds_adapter.test_connection()
            
            # 3. Execute query
            qr = ds_adapter.execute(self.result_query)
            
            # 4. Ensure keys are populated
            if not qr.keys and qr.rows:
                if isinstance(qr.rows[0], dict):
                    qr = QueryResult(
                        keys=list(qr.rows[0].keys()),
                        rows=qr.rows,
                        query_time_seconds=qr.query_time_seconds,
                        last_data_update=qr.last_data_update
                    )
            
            # 5. Write output
            ctx = OutputWriteContext(
                sheet_name='Resultaat',
                title=self.title,
                # ... more context
            )
            out_adapter.write_report(ctx, qr)
            
            # 6. Update history
            self._update_history(qr)
            
            # 7. Send mail
            if sender:
                sender.send(self._mail_body(qr))
                
        except Exception as e:
            logging.error(f"[{self.name}] Failed: {e}")
            raise
```

**Key Points:**
- Adapters are created fresh per report (factory pattern)
- Keys are inferred if empty (but datasources SHOULD populate them)
- `OutputWriteContext` passes metadata to output adapter
- History/summary updated post-write
- Exceptions bubble up (orchestrator retries)

---

## Datasource Adapters

### Contract (Datasource Protocol)

```python
class Datasource(Protocol):
    """Any datasource must implement this."""
    
    name: str
    
    def test_connection(self) -> None:
        """Raise exception if connection fails."""
    
    def execute(self, query: str) -> QueryResult:
        """Execute query; return QueryResult."""
```

---

### ArangoDB Adapter

**Location:** `datasources/arango.py`  
**Connection:** `SingleArangoConnector` singleton

**Responsibilities:**
1. Test ArangoDB connectivity
2. Execute AQL query
3. Populate `keys` from result
4. Populate `last_data_update` from `params` collection

**Implementation Checklist:**
```python
class ArangoDatasource:
    def __init__(self, connector=None):
        self.connector = connector or SingleArangoConnector.get_connector()
        self.name = 'ArangoDB'
    
    def test_connection(self) -> None:
        """Test ArangoDB reachability."""
        try:
            db = self.connector.db
            db.collections()  # Simple query
        except Exception as e:
            raise ConnectionError(f"ArangoDB unreachable: {e}")
    
    def execute(self, query: str) -> QueryResult:
        """Execute AQL query."""
        start = time.time()
        
        try:
            db = self.connector.db
            cursor = db.aql.execute(query)
            rows = list(cursor)  # list of dicts
            
            # Extract keys from first row
            keys = list(rows[0].keys()) if rows else []
            
            # Get last_data_update from params
            last_data_update = self._get_last_data_update()
            
            query_time = time.time() - start
            
            return QueryResult(
                keys=keys,
                rows=rows,
                query_time_seconds=query_time,
                last_data_update=last_data_update
            )
        except Exception as e:
            logging.error(f"AQL execute failed: {e}")
            raise
    
    def _get_last_data_update(self) -> str | None:
        """Get last sync time from params collection."""
        try:
            db = self.connector.db
            doc = db.collection('params').document('finished_at')
            return doc.get('value')  # ISO timestamp
        except:
            return None
```

**Key Points:**
- ✅ MUST populate `keys` from `rows[0].keys()`
- ✅ MUST populate `last_data_update` from `params.finished_at`
- ✅ MUST measure `query_time_seconds`
- Rows are dicts; output adapters convert as needed

---

### PostGIS Adapter

**Location:** `datasources/postgis.py`  
**Connection:** Connection pooling via `SinglePostGISConnector`

**Responsibilities:**
1. Test PostgreSQL connectivity
2. Execute SQL query with error recovery
3. Populate `keys` from cursor.description
4. Populate `last_data_update` from connector metadata

**Implementation Checklist:**
```python
class PostGISDatasource:
    def __init__(self, connector=None):
        self.connector = connector or SinglePostGISConnector.get_connector()
        self.name = 'PostGIS'
    
    def test_connection(self) -> None:
        """Test PostgreSQL reachability."""
        try:
            conn = self.connector.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
        except Exception as e:
            raise ConnectionError(f"PostGIS unreachable: {e}")
    
    def execute(self, query: str) -> QueryResult:
        """Execute SQL query with rollback recovery."""
        start = time.time()
        
        try:
            conn = self.connector.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Fetch all rows
            rows = cursor.fetchall()  # list of tuples
            
            # Extract keys from cursor.description
            keys = [col[0] for col in cursor.description]
            
            # Get last_data_update
            last_data_update = self.connector.get_params().get('last_update_utc_assets')
            
            query_time = time.time() - start
            cursor.close()
            
            return QueryResult(
                keys=keys,
                rows=rows,  # tuples, not dicts
                query_time_seconds=query_time,
                last_data_update=last_data_update
            )
        
        except psycopg2.InternalError as e:
            # Transaction abort; rollback and retry once
            logging.warning(f"Transaction aborted; rolling back: {e}")
            conn.rollback()
            # Retry (simple approach; consider backoff)
            return self.execute(query)
        
        except Exception as e:
            logging.error(f"SQL execute failed: {e}")
            raise
```

**Key Points:**
- ✅ MUST populate `keys` from `cursor.description`
- ✅ MUST populate `last_data_update` from connector metadata
- ✅ MUST handle transaction abort with rollback + retry
- Rows are tuples; output adapters convert as needed

---

## Output Adapters

### Contract (Output Pattern)

```python
class OutputAdapter(Protocol):
    """Any output adapter must implement this."""
    
    def write_report(self, ctx: OutputWriteContext, qr: QueryResult) -> None:
        """Write QueryResult to output destination."""
```

**OutputWriteContext:**
```python
@dataclass
class OutputWriteContext:
    sheet_name: str              # e.g., 'Resultaat'
    title: str                   # e.g., 'Asset Report'
    summary_sheet_id: str        # Sheet ID for 'Overzicht'
    history_sheet_id: str        # Sheet ID for 'Historiek'
    persistent_column: str | None = None  # e.g., 'C' for user notes
```

---

### Excel Adapter (New)

**Location:** `outputs/excel.py`

**Responsibilities:**
1. Create .xlsx file locally
2. Write header row + data rows
3. Format (optional: colors, fonts)
4. Upload to OneDrive/SharePoint

**Implementation Sketch:**
```python
class ExcelOutput:
    def __init__(self, upload_config=None):
        self.upload_config = upload_config
        self.name = 'Excel'
    
    def write_report(self, ctx: OutputWriteContext, qr: QueryResult) -> None:
        """Write QueryResult to Excel and upload."""
        
        # 1. Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = ctx.sheet_name[:31]  # Max 31 chars
        
        # 2. Write header
        ws.append(qr.keys)
        
        # 3. Write rows (memory-efficient for large datasets)
        for row_data in qr.iter_rows():
            ws.append(row_data)
        
        # 4. Save locally
        temp_file = f"/tmp/report_{ctx.sheet_name}.xlsx"
        wb.save(temp_file)
        
        # 5. Upload
        self._upload_to_onedrive(temp_file, ctx)
    
    def _upload_to_onedrive(self, local_file: str, ctx: OutputWriteContext) -> None:
        """Upload file to OneDrive/SharePoint."""
        # Placeholder: integrate MS Graph API
        # For now, copy to configured network path
        pass
```

**Memory Strategy:**
- **Small datasets (<1000 rows):** Use `qr.to_rows_list()`, load all in memory
- **Large datasets (>1000 rows):** Use `qr.iter_rows()`, stream to file

**Example:**
```python
# For large datasets
for row in qr.iter_rows():  # Generator; no OOM
    ws.append(row)
```

---

## QueryResult & Conversion

### QueryResult Dataclass

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class QueryResult:
    keys: list[str]
    rows: list[Sequence[Any] | dict[str, Any]]
    last_data_update: str | None = None
    query_time_seconds: float | None = None
    
    def to_rows_list(self) -> list[list[Any]]:
        """Convert all rows to list[list] format."""
        if not self.rows:
            return []
        
        first = self.rows[0]
        if isinstance(first, dict):
            # Dicts: order by keys
            return [[row.get(k) for k in self.keys] for row in self.rows]
        else:
            # Tuples/lists: convert to lists
            return [list(row) for row in self.rows]
    
    def iter_rows(self):
        """Memory-efficient iterator over rows as lists."""
        for row in self.rows:
            if isinstance(row, dict):
                yield [row.get(k) for k in self.keys]
            else:
                yield list(row)
```

### Conversion Responsibility

| Format | Source | Adapter | Handling |
|---|---|---|---|
| dict | ArangoDB | ArangoDatasource | Populate keys from dict.keys() |
| tuple | PostGIS | PostGISDatasource | Populate keys from cursor.description |
| list[list] | Output | ExcelOutput (or others) | Use qr.to_rows_list() or iter_rows() |

---

## Configuration & Settings

### settings.json Schema

```json
{
  "databases": {
    "arango": {
      "host": "localhost",
      "port": 8529,
      "user": "root",
      "password": "${ARANGO_PASSWORD}",
      "dbname": "asset_db"
    },
    "postgis": {
      "host": "localhost",
      "port": 5432,
      "user": "gis_user",
      "password": "${POSTGIS_PASSWORD}",
      "dbname": "gis_db"
    }
  },
  "output": {
    "type": "excel",
    "excel": {
      "upload_type": "onedrive",
      "onedrive": {
        "base_path": "/Shared Documents/Reports",
        "credentials_file": "~/.credentials/onedrive.json"
      }
    }
  },
  "report_execution": {
    "mode": "sequential",
    "max_concurrent": 2,
    "timeout_seconds": 1800
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_base_seconds": 2
  },
  "mail": {
    "enabled": true,
    "smtp_server": "mail.company.com",
    "smtp_port": 587,
    "from": "reports@company.com",
    "recipients": ["admin@company.com"]
  },
  "time_window": {
    "start_hour": 5,
    "end_hour": 23
  }
}
```

### Environment Variables

Sensitive credentials use environment variables:
```bash
export ARANGO_PASSWORD="secret"
export POSTGIS_PASSWORD="secret"
export ONEDRIVE_CREDENTIALS_FILE="/etc/rsa/onedrive.json"
```

Reference in settings.json:
```json
{
  "password": "${ARANGO_PASSWORD}"
}
```

### Loading Configuration

```python
from SettingsManager import SettingsManager

settings = SettingsManager.load('/path/to/settings.json')
arango_config = settings['databases']['arango']
# ... use config
```

---

## Logging Strategy

### Context Injection (ContextVar)

Each report adds context to all logs without manual threading:

```python
from contextvars import ContextVar

_report_context = ContextVar('report_name', default='system')

def set_report_context(name: str):
    _report_context.set(name)

def get_report_context():
    return _report_context.get()
```

### Custom Filter

```python
import logging

class ReportContextFilter(logging.Filter):
    """Injects report name into all log records."""
    
    def filter(self, record):
        record.report_name = get_report_context()
        return True

# Setup
logger = logging.getLogger()
logger.addFilter(ReportContextFilter())

# Log format
formatter = logging.Formatter(
    '[%(asctime)s] [%(report_name)s] %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
```

### Example Output

```
[2026-03-30 16:32:20] [Report0002] INFO - Starting report
[2026-03-30 16:32:21] [Report0002] INFO - Query executed in 1.2s (54 rows)
[2026-03-30 16:32:22] [Report0002] INFO - ✓ Completed successfully
[2026-03-30 16:32:23] [Report0004] INFO - Starting report
[2026-03-30 16:32:24] [Report0004] ERROR - Connection failed (retry 2/3)
```

---

## Testing & Mocking

### Unit Test Pattern (Datasource)

```python
import pytest
from unittest.mock import Mock
from datasources.arango import ArangoDatasource
from datasources.base import QueryResult

def test_arango_execute():
    # Mock connector
    mock_connector = Mock()
    mock_connector.db.aql.execute.return_value = [
        {'id': '1', 'name': 'Asset1'},
        {'id': '2', 'name': 'Asset2'},
    ]
    
    # Create adapter with mock
    ds = ArangoDatasource(connector=mock_connector)
    
    # Execute
    qr = ds.execute("FOR v IN assets RETURN v")
    
    # Assert
    assert qr.keys == ['id', 'name']
    assert len(qr.rows) == 2
    assert qr.query_time_seconds > 0
```

### Integration Test Pattern (Output)

```python
def test_excel_write():
    # Create QueryResult
    qr = QueryResult(
        keys=['id', 'name'],
        rows=[('1', 'Asset1'), ('2', 'Asset2')],
        query_time_seconds=1.5,
        last_data_update='2026-03-30T12:00:00Z'
    )
    
    # Create adapter
    output = ExcelOutput()
    
    # Write to temp file
    ctx = OutputWriteContext(
        sheet_name='Test',
        title='Test Report'
    )
    output.write_report(ctx, qr)
    
    # Verify file exists and has data
    # ...
```

---

## Creating a New Report

### Checklist

- [ ] File: `Reports/ReportXXXX.py`
- [ ] Class: `ReportXXXX` (matches filename)
- [ ] Inherit from or wrap `DQReport`
- [ ] Implement `init_report()` → populate `self.report`
- [ ] Implement `run_report(sender)` → call `self.report.run_report(sender)`
- [ ] Define `result_query` (AQL or SQL)
- [ ] Test locally: `python run_single_report.py --once --report ReportXXXX`

### Template

```python
from lib.reports.DQReport import DQReport

class ReportXXXX:
    """Description of the report."""
    
    def init_report(self):
        """Initialize report with datasource and output."""
        self.report = DQReport(
            name='report_xxxx',
            title='Report Title Here',
            spreadsheet_id='sheet_id_or_path',  # For output routing
            datasource='ArangoDB',  # or 'PostGIS'
            output='excel'
        )
        
        # Define query
        self.report.result_query = """
            FOR v IN collection_name
            LIMIT 1000
            RETURN { id: v._id, name: v.name }
        """
    
    def run_report(self, sender):
        """Execute report."""
        self.report.run_report(sender=sender)
```

### Testing the Report

```bash
# Run once (exits after completion)
python run_single_report.py --once --report ReportXXXX

# Check logs
tail -f logs.txt | grep ReportXXXX
```

---

## Backwards Compatibility

### Legacy Report Migration

If migrating an old `LegacyReport` to `DQReport`:

1. Extract query from legacy class
2. Move to `result_query` in new `DQReport`
3. Ensure datasource is correct (ArangoDB, PostGIS)
4. Test output matches baseline
5. Deploy; monitor for 1 run cycle

### Neo4j Phaseout

Neo4j imports are still present but:
- ❌ Not actively used in production
- ⚠️ Marked as deprecated
- 📋 Plan: Phase out by Q3 2026

Old Neo4j reports preserved in `ArchivedReports/` for reference.



