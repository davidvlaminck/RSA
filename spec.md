# Specificatie: refactoring en requirements

## Doel

Dit document beschrijft de functionele en niet-functionele eisen voor de refactor van de rapporteringsservice. De belangrijkste doelstellingen zijn: betere uitbreidbaarheid, betrouwbaarheid (nooit stilvallen bij fouten), ondersteuning voor meerdere output-backends (Google Sheets en Excel/OneDrive/SharePoint) en een heldere scheiding tussen datasource-implementaties (ArangoDB, PostGIS).

## Scope

- Refactor van de core rapport-architectuur en datasources.
- Output: Google Sheets (bestaand) + Excel-bestanden waarbij Excel-bestanden lokaal worden aangemaakt en geüpload/gesynchroniseerd via OneDrive/SharePoint.
- Datasources: ArangoDB en PostGIS (onafhankelijk van elkaar). Neo4j is historisch aanwezig en wordt niet in scope gebracht tenzij expliciet gevraagd.
- Robuuste uitvoer (retry, logging, foutafhandeling, notificatie).

## 1. Functionele eisen (FR)

**FR1 - Meerdere output-backends**

- De service moet Google Sheets blijven ondersteunen.
- De service moet ook Excel-rapportage ondersteunen: het rapport wordt lokaal gerenderd als .xlsx en vervolgens geüpload naar een OneDrive/SharePoint-locatie of geplaatst op een bestandslocatie die door een sync-agent (vanuit de organisatie) geconsumeerd wordt.
- Output-adapters moeten uitbreidbaar zijn (interface/abstract class).

**FR2 - Datasource-abstractie**

- Datasource-adapters voor ArangoDB en PostGIS moeten bestaan en onafhankelijk werken.
- Elke adapter moet minimaal twee methoden bieden: `test_connection()` en `execute(query)`.
- De `execute()` methode moet een eenduidig QueryResult-object retourneren met minimaal: `rows` (list), `keys` (list), `query_time_seconds` (float) en `last_data_update` (str, ISO).

**FR3 - Tijdwindow run en pipeline script**

- Er moet een CLI/script (vergelijkbaar met `ReportLoopRunner`) dat de rapport-run start. Daarnaast moet er een speciale run-mode die tussen configurable tijdsgrenzen (bv. tussen 03:01 en 05:00) een ander script uitvoert dat de database opnieuw vult.
- De tijdwindow moet configureerbaar via een settings/config-bestand.
- NB: Het verwijderen van params in ArangoDB gebeurt in een externe repo/pipeline, niet in deze repo.

**FR4 - Retry en foutafhandeling**

- Een rapport-run mag nooit stilvallen: bij fouten moet er een retry-mechanisme zijn met exponentiële backoff en een configureerbaar maximum aantal pogingen.
- Als een rapport na N pogingen nog faalt, moeten de foutlogs worden geüpload naar een centrale opslag (S3 of alternatieve cloud opslag) en een notificatie worden gestuurd.
- Fouten in één rapport mogen de andere rapporten in de batch niet stoppen (isolation/fail-fast per-report but continue overall).

**FR5 - Mail-notificaties**

- Na een volledige run moeten e-mails worden gestuurd via de bestaande `MailSender`-functiealiteit.
- Mailcontent bevat samenvatting: aantal resultaten per rapport en last_data_update per datasource.

**FR6 - Historiek en samenvatting**

- Historiek-sheet (`Historiek`) en summary (`Overzicht`) moeten bijgewerkt blijven met: now_utc, last_data_update en aantal rijen.
- Voor ArangoDB-rapporten moet `last_data_update` afgeleid worden van `params` collectie (attribuut `finished_at`) wanneer die beschikbaar is.
- Voor PostGIS-rapporten moet `last_data_update` afgeleid worden via `SinglePostGISConnector.get_params()` (attribuut `last_update_utc_assets`).

## 2. Niet-functionele eisen (NFR)

**NFR1 - Betrouwbaarheid**

- Retries, transactie-rollback (indien relevant) en resource cleanup moeten gegarandeerd worden.

**NFR2 - Observeerbaarheid**

- Alle belangrijke stappen (start/stop per rapport, fouten, retries, upload logs) moeten in logfiles met timestamp worden vastgelegd.
- Bij upload van logs moet het upload-resultaat ook gelogd worden.

**NFR3 - Testbaarheid**

- Unit-tests en integratietests voor datasource-adapters (mocked DBs) en output-adapters moeten mogelijk zijn.

**NFR4 - Extensibility**

- Architectuur moet OOP en dependency-injection vriendelijk zijn: nieuwere adapters moeten zich eenvoudig implementeren door een interface te volgen.

**NFR5 - Performance**

- Gebruik afgeleide edge-collecties in ArangoDB voor grote traversals. Traversals op `assetrelaties` die niet gefilterd zijn zijn te traag en moeten vermeden worden.

## 3. Data contracts en QueryResult

**TODO: bespreek met AI**

**QueryResult object (contract returned by datasource.execute):**

- `rows`: list[dict] of list[values] — resultaat-rijen; voor ArangoDB perfer dicts {key: value}.
- `keys`: list[str] — header keys (kan leeg zijn voor ArangoDB maar `DQReport` zal infereren keys uit `rows[0]`).
- `query_time_seconds`: float — uitvoeringstijd in seconden.
- `last_data_update`: str | None — ISO timestamp van de laatste synchronisatie van die datasource (kan uit `params` komen).

## 4. Configuratie en settings

- Centraal `settings.json` (of `.yaml`) met:
  - databases: instellingen voor ArangoDB en PostGIS (host, user, password, dbname)
  - output: Google Sheets credentials, OneDrive/SharePoint credentials (of upload target)
  - scheduling: tijdwindows, frequency defaults
  - retry policy: max_retries, backoff_base_seconds
  - logging: remote_upload_target (S3 bucket or other), retention

## 5. Implementatie notes / aanbevolen aanpak

- **Datasource adapters:**
  - `ArangoDatasource`:
    - Implement `test_connection()` and `execute(aql_string)` returning QueryResult.
    - When executing long traversals prefer using derived edge collections such as `voedt_relaties`.
    - Populate `last_data_update` from `params` collection (`finished_at`).
  - `PostGISDatasource`:
    - Implement connection pooling (existing `SinglePostGISConnector`) and safe transaction handling.
    - Implement reset/rollback strategy when encountering `current transaction is aborted` errors.

- **Output adapters:**
  - `GoogleSheetsOutput` (existing)
  - `ExcelOutput`:
    - Generate `.xlsx` file locally (e.g., with openpyxl or xlsxwriter).
    - Upload to OneDrive/SharePoint using available corporate API or an upload helper (configurable).
    - Keep the same OutputWriteContext contract so `DQReport` can call `out.write_report(...)` unchanged.


- **Logging and upload:**
  - Implement structured logging (JSON lines) and a log-archiver that, after N failed retries, uploads the collected logs to the configured remote target.

## 6. Acceptance criteria

- All existing reports still run and their outputs are equivalent (Google Sheets behavior preserved).
- Excel output option implemented and verified for at least one report, including upload to the configured target.
- ArangoDB adapter returns `QueryResult` objects with `rows` and `keys` inferred if missing; `last_data_update` populated from `params.finished_at` when available.
- PostGIS adapter returns `QueryResult` objects with `last_data_update` populated from `SinglePostGISConnector.get_params()` (attribuut `last_update_utc_assets`).
- Retry logic tested: simulate a failing report, verify retries and final log upload.
- Mail notifications are sent after a full run with summary of results and last_data_update per datasource.

## 7. Rollout plan (phased)

**Phase 0: Tests and infra preparation**

- Add unit tests for adapters and QueryResult contract.
- Add/verify config schema and credentials placement.

**Phase 1: Adapter & Output scaffolding**

- Implement `ArangoDatasource` and `ExcelOutput` scaffolds.
- Keep GoogleSheetsOutput unchanged.
- Verify PostGIS adapter correctly populates `last_data_update` from `get_params()`.

**Phase 2: Timed run mode**

- Implement CLI/script with configurable timewindow support for triggering external database-fill scripts.
- Test timewindow logic and integration with external pipeline.

**Phase 3: Monitoring and hardening**

- Implement log-archive upload and verify retry behaviors and notifications.
- Finalize documentation and runbook.

## 8. Toelichting / opmerkingen

- Neo4j: veel oude code gebruikt Neo4j; behoud oude query-strings in `ArchivedReports/` for reference, but do not keep Neo4j in the primary runtime unless explicitly required.
- Security: be careful with credential storage; use environment variables or a secure vault for production secrets.
