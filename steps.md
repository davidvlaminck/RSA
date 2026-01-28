# Steps for Refactoring Reports to Use AQL Queries (Updated)

## 1. Overview
Refactor all report files in the `Reports` folder to use their `aql_query` as the main query, and preserve the original Cypher query for reference. The data source should be set to `ArangoDB`. The persistent column should be set to the first column after the last data column returned by the AQL query.

## 2. Steps

### Step 1: Identify Files
- For each file in the `Reports` folder:
  - Check if the file contains an `aql_query` variable or an AQL query block.

### Step 2: Refactor Report Class
- If an AQL query is present:
  - Move the AQL query definition inside the `init_report` function (do not use a global variable).
  - Assign the AQL query directly to `self.report.result_query` inside `init_report`.
  - Add a new attribute `cypher_query` to the report, containing the original Cypher query (the previous value of `result_query`).
  - Change the `datasource` attribute to `ArangoDB`.

### Step 3: Adjust Persistent Column
- Parse the AQL query to count the number of columns returned in the `RETURN` statement.
- Set the `persistent_column` attribute to the column letter immediately after the last data column (e.g., if 2 columns, use 'C').

### Step 4: Save and Test
- Save the changes to the file.
- Ensure the report still runs as expected.

## 3. Example
For `Report0002.py`:
- The AQL query returns `{ uuid: a._key, naam: a.AIMNaamObject_naam }` (2 columns: uuid, naam).
- Set `persistent_column` to 'C'.
- Set `datasource` to 'ArangoDB'.
- Set `result_query` to the AQL query (inside `init_report`).
- Add `cypher_query` with the original Cypher query.

## 4. Next Steps
- Try this process for one report file.
- If successful, apply to all report files in the folder.
