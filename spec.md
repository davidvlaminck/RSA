# Refactoring Specification: Reporting pipeline

## 1. Background

### 1.1 Existing use case (current)
- Generate **Google Sheets** with report data.
- Data sources:
  - **Neo4j** (some reports)
  - **PostGIS** (most reports)
- After a **full report run**, send email notifications with the outcome.

### 1.2 Target use case (new)
- Generate **Microsoft Excel workbooks (.xlsx)** with report data.
- Data sources:
  - **ArangoDB** (most reports)
  - **PostGIS** (some reports; its own sync schedule)
- Deliver the generated Excel files by uploading to:
  - **OneDrive** and/or **SharePoint**
- After a **full report run**, send email notifications with the outcome.

## 2. Goals
- Replace the current Google Sheets output with **Excel output**.
- Replace Neo4j as a datasource with **ArangoDB**.
- Provide a fully automated, scheduled process that:
  1) refreshes ArangoDB from the API daily
  2) generates and uploads Excel reports daily
  3) sends a run summary email after the full run completes
- Improve operational quality:
  - robust **logging**
  - clear **error handling**
  - repeatable, file-based deployment (git update + run)
- Ensure that data in the Resultaat sheet is only wiped if new data can be written. If anything goes wrong during the update, the previous version of the sheet must be automatically restored (fallback/revert functionality).
- Only one summary email should be sent per run, not multiple.

## 3. Scope

### 3.1 In scope
- Running report queries against ArangoDB and PostGIS.
- Generating Excel workbooks from report results.
- Uploading workbooks to OneDrive/SharePoint.
- Sending email notifications after a full report run.
- Scheduling/automation of the refresh + reporting jobs.
- Query migration where needed (Neo4j/Cypher → Arango/AQL).
- Ensuring the **fixed “comments” column is always the last column** in exported spreadsheets.

### 3.2 Out of scope / non-goals
- Replacing the PostGIS upstream sync schedule and mechanism.
- Building interactive dashboards (this is a batch export pipeline).
- Manual spreadsheet editing workflows (the pipeline overwrites/uploads outputs).

## 4. Terminology
- **Report**: a named unit that produces a tabular dataset (rows + columns) using a query.
- **Datasource**:
  - **ArangoDB**: primary datasource for most reports.
  - **PostGIS**: secondary datasource for some reports.
- **Workbook**: a generated Excel `.xlsx` file containing one or more worksheets.
- **Full report run**: execution of the complete configured set of reports for a scheduled run.
- **Persistent/comment column**: a column reserved for human comments that must remain the **last** column.

## 5. Functional requirements

### FR1 — Datasources
- The system must support querying:
  - ArangoDB (AQL)
  - PostGIS (SQL)
- Each report must declare exactly one datasource.

### FR2 — Output format (Excel)
- The system must create Excel `.xlsx` files.
- Each report must map to a worksheet or a dedicated workbook (implementation choice), but the output must be Excel.

### FR3 — Upload destinations
- The system must upload generated Excel files to **OneDrive** or **SharePoint**.
- Upload must support overwrite or versioned uploads (choose one; default: overwrite).

### FR4 — Scheduling / automation
- The process must be automated and scheduled with the following daily sequence:
  1. **03:01** — erase and reload ArangoDB from the API.
  2. **05:00** — generate the Excel spreadsheets and upload them.
- PostGIS syncing is external and has its own schedule.

### FR5 — Query migration and column alignment
- When converting existing reports from Neo4j/Cypher (or other formats) to ArangoDB/AQL:
  - exported columns must be updated accordingly.
  - the reserved “comments” column must always remain the **final** column in the worksheet.

### FR6 — Deployment model (git update + run)
- The process must be runnable from a git checkout and support automated updates:
  - pull/update code from a git repository
  - run without manual editing
- Code should be structured to be **importable as a module** (file-based, not only ad-hoc scripts).

### FR7 — Email notifications after full run
- After completing a full report run, the system must send an email containing at least:
  - overall run status (success/failed/degraded)
  - start/end timestamps and total duration
  - per-report status (success/failure), row count, and runtime
  - upload status (where the files were uploaded)
- Email sending must work for both the current and target use cases.

### FR8 — Resultaat sheet data integrity and fallback
- The system must only clear (wipe) the Resultaat sheet if new data is available and can be written successfully.
- If any error occurs during the update, the system must automatically revert the sheet to its previous version to prevent data loss.

## 6. Non-functional requirements

### NFR1 — Logging
- The system must log:
  - start/end of each scheduled job
  - start/end of each report
  - upload success/failure and destination
  - email send attempt + success/failure
  - row counts per report
  - timing (duration) per major step

### NFR2 — Error handling and reliability
- Failures must be handled with clear behavior, at minimum:
  - If the Arango refresh fails, the 05:00 reporting job should either:
    - not run, or
    - run in “best effort” mode using existing data (decision required; default: do not run).
  - If a single report fails, other reports should still run (best effort).
  - Upload failures should be retried (configurable retry count).
  - If email sending fails, it must be logged clearly and must not silently pass.

### NFR3 — Idempotency
- Re-running the same job should not create duplicated output.
- Rebuild steps (e.g., Arango refresh) must be safely repeatable.

### NFR4 — Configuration
- Credentials and endpoints must not be hard-coded.
- Configuration should support environment-based deployment (dev/test/prod).

### NFR5 — Notification uniqueness
- The system must ensure that only one summary email is sent per report run, and must not send duplicate notifications for the same run.

## 7. Data flow (high level)
1) **Arango refresh job**
   - Clear ArangoDB data.
   - Re-import from API.

2) **Report generation job**
   - For each report:
     - run query against its datasource
     - normalize results to a tabular shape
     - generate/update Excel worksheet
     - ensure comments column is last
   - Upload workbooks to OneDrive/SharePoint.
   - Send a summary email after the full run completes.

## 8. Acceptance criteria
- A daily scheduler triggers:
  - Arango reload at 03:01
  - report generation + upload at 05:00
- Reports can pull data from ArangoDB (AQL) and PostGIS (SQL).
- Output is valid `.xlsx` and contains all expected columns.
- The comments/persistent column is always the last column after any query migration.
- Upload to OneDrive/SharePoint succeeds and is logged.
- After the full report run, a summary email is sent and is logged.
- Failures are logged with actionable messages and do not silently pass.
