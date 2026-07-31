# Plan RSA_Health — Signal-based Pipeline Orchestrator

Verplichet van `RSA_Health/orchestrator.md` (signal-based, SQLite-driven pipeline).
Dit plan legt uit welke zaken al geïmplementeerd zijn, wat nog mist, en hoe dat hier (in deze repo **RSA**) én in de bijbehorende repos afgestemd wordt.

## Scope & verantwoording

`orchestrator.md` beschrijft een pipeline die zich over meerdere onafhankelijke services verspreidt. De centrale bron van waarheid (`pipeline_state` in SQLite) en de FastAPI-orchestrator leven in **RSA_Health**; de **RSA**-reportservice rapporteert hieraan. Dit plan volgt dat scheidingslijn-schetting:

| Component | Repo | Eigenaar plan |
|---|---|---|
| FastAPI server (`/pipeline/update`, `/pipeline/state`, `/health`, `/history`), `pipeline_state`-tabel, health-dashboard | `RSA_Health` | RSA_Health |
| Achtergrond-orchestrator (drive-steps, sequencing, midnight-reset, Power-Automate markers) | `RSA_Health` | RSA_Health |
| PostgreSQL pause/resume van `AWVInfraPostGISSyncer` | `AWVInfraPostGISSyncer` | AWVInfraPostGISSyncer (extern) |
| Arango-sync (rapporteert `arango_sync`) | `InfraDbToArangoDb` | InfraDbToArangoDb (extern) |
| RSA-reportservice: rapporteert `rsa_queries`, respecteert preconditions | `RSA` (deze repo) | RSA |
| Power Automate (SharePoint↔Drive marker-bestanden) | extern (Microsoft) → via Drive | Power Automate |

> Dit plan wordt in de **RSA**-repo vertrokken, maar benoemt alle owners. De RSA-specifieke taken staan in §3 (RSA-taken) en worden in de implementatievolgorde in §4 gehonoreerd.

## Huidige stand van implementatie (audited 2026-07-31)

### RSA_Health — grotendeels klaar
- `main.py` → `pipeline_state`-tabel met `CHECK(id=1)`, seed-rij `idle`/`completed` → **Stap 1 ✓**
- `POST /pipeline/update` + `GET /pipeline/state` → **Stap 2 ✓**
- `static/index.html` polled `/pipeline/state` iedere 5s en rendert een "Pipeline Status" kaart (fase/status/updated_at/message) → **Stap 3 ✓**
- `run_arango_sync()` voert Arango-sync uit en rapporteert `arango_sync` running/sub-stappen/completed/failed → **Stap 4 gedeeltelijk**. *N.B.:* dit is het **synchrone** model; `orchestrator.md` verzoekt Arango-sync als **onafhankelijke service** die zijn status zelf rapporteert (in `InfraDbToArangoDb`). De huidige functie dient als startpunt/volgorde, maar moet oorgaan aan een zelfstandige reporter (zie open taak).
- Geen achtergrond-orchestrator → **Stap 8 ✗**
- Geen daily midnight-reset → ✗
- Geen PostGIS pause/resume, geen Power-Automate marker-detectie → **Stap 7 ✗ / Stap 6 ✗**

### RSA (deze repo) — RSA-queries-service
- `lib/reports/pipeline_status.py` → `PipelineStatusReporter` POST’t naar `http://localhost:8000/pipeline/update` → **Stap 2-student kant ✓ (in RSA zelf)**
- `lib/reports/ReportLoopRunner.py` (`run()`, ~15:240) rapporteert `rsa_queries` running/completed/failed via `self.pipeline_status` → **Stap 5 gedeeltelijk ✓**
- `scripts/ops/gdrive_upload.py` → `sync_drive_to_local` (drive_download) en `sync_local_to_drive` (drive_upload) bestaan.
- `main.py` → `DailyDriveSyncGate` (drive_download) en `upload_after_run` (drive_upload) zijn **callbacks** in de RSA-loop en rapporteren hun fase **niet** aan `pipeline_status`, en controleren de pipeline-preconditons ook **niet** → **onvolledig**.
- `settings_sample.json` → heeft **geen** `pipeline_status`-blok (moet `base_url`/timeout configureren) → ✗

## RSA-taken (wat deze repo moet doen)

Deze taken zijn de verantwoordelijkheid van de RSA-repo en vormen de minimale invulling van stap 5 + de integrationspunten voor de orchestrator.

### T1 — `pipeline_status`-config toevoegen aan settings
- `settings_sample.json` + `settings_parallel_example.json`: blok `pipeline_status` { `enabled`, `base_url` (default `http://localhost:8000`), `timeout_seconds` (default 5) }.
- `SettingsManager` blijft settings als dict doorgeven; `PipelineStatusReporter.__init__` leest het blok (reeds gebeuren in `pipeline_status.py:16`).
- Rationale: zonder config faalt reporting stilletjs in prod (base_url zal anders zijn dan localhost).

### T2 — RSA rapporteert drive-phases aan de orchestrator
- In `main.py` `DailyDriveSyncGate.ensure_synced`: bij start `drive_download`/`running`, bij succes `drive_download`/`completed`, bij falen `drive_download`/`failed`.
- In `main.py` `upload_after_run`: `drive_upload`/`running` → `completed`|`failed`.
- Gebruik `PipelineStatusReporter` (instantieer in `main.py`, of hergebruik de in `ReportLoopRunner`). Hergebruik via een kleine shared helper `lib/reports/pipeline_status.py` functie of een repo-level singleton zodat `main.py` en `ReportLoopRunner` dezelfde base_url/timeout nemen.

### T3 — RSA wacht op preconditions vóór rapportage start
- `orchestrator.md` regel ~226: RSA moet wachten tot `drive_download = completed` **en** `postgis_sync = paused` (of `postgis_sync_running` buiten de pauze-periode) is.
- Implementatie-optie (klein): `ReportLoopRunner` vraagt `GET /pipeline/state` op vóór `run()`. Huidige `_is_within_run_window(05:00–23:59)` blijft als **time-based fallback**, maar de signal-based gating heeft voorrang. Respecteer een timeout (bijv. wacht-max. via setting `pipeline_status.wait_timeout_seconds`, default 7200s) en rapporteer `aborted` bij expiry.
- Idempotentie: alleen rapporteren wanneer de fase zich daadwerkelijk wijzigt.

### T4 — RSA rapporteert fase-overgangen en fouten robuust
- Bestaande `rsa_queries` reporting in `run()` blijft; zorg dat `failed` incl. exception-message wordt gemeld (reeds zo, `str(exc)`).
- Voeg optionele finer-grained sub-statussen toe (bv. per datasource) via `message`-veld, zonder nieuwe fasen.

### T5 — Tests
- `UnitTests/` → test `PipelineStatusReporter.update` met mocked `requests.post` (verifieer payload `phase/status/message` en auth/header‑behaviour). Er is nog geen test voor `pipeline_status.py`; voeg `test_pipeline_status.py` toe.
- Test `DailyDriveSyncGate` + `upload_after_run` integratie met een stub `PipelineStatusReporter` om fase-transitie calls te assert-en.

## Stappen uit `orchestrator.md` → status & owner

| Stap | Omschrijving | Status | Owner |
|---|---|---|---|
| 1 | SQLite `pipeline_state`-tabel + seed | ✓ (Stap 1 @ RSA_Health) | RSA_Health |
| 2 | `POST /pipeline/update` endpoint | ✓ (Stap 2 @ RSA_Health) | RSA_Health |
| 3 | Health-pagina polling van fase/status | ✓ (Stap 3 @ RSA_Health index.html) | RSA_Health |
| 4 | Arango-sync rapporteert `arango_sync` | ~ (sync functie bestaat; moet onafh. service + reporter worden) | InfraDbToArangoDb |
| 5 | RSA ReportLoopRunner = onafh. service rapporteert `rsa_queries`, wacht op preconditions | ~ (reporting ✓; preconditions ✗) | RSA (T3) |
| 6 | Power-Automate via Drive marker-bestanden | ✗ (detectie ontbreekt) | RSA_Health (marker polling) + Power Automate |
| 7 | PostGIS sync pauzeren/hervatten via `pipeline_state` | ✗ (sync script leest fase) | AWVInfraPostGISSyncer |
| 8 | Achtergrond-orchestrator (drive-steps, sequencing, reset, markers) | ✗ | RSA_Health |
| +midnight | Dagelijkse reset om middernacht | ✗ | RSA_Health |

## Implementatievolgorde (prioriteit)

Gewicht: prioriteit binnen deze repo (RSA) eerst, rest als afhankelijkheid/blok.

1. **RSA:** T1 — `pipeline_status`-config (settings_sample.json + parallel). *Laag risico, blokkeert niet, maar verplicht voor prod.*
2. **RSA:** T2 — drive-phases rapporteren vanuit `main.py` (T1 eerst).
3. **RSA_Health:** Stap 8/6 — orchestrator + Power-Automate marker polling. *(Blok voor RSA precondition-waits, want `drive_download`/`completed` en `postgis_sync`/`paused` komen uit de orchestrator.)*
4. **RSA_Health:** Stap 7 — PostGIS pause/resume endpoint/signaling. *(Blok voor RSA precondition `postgis_sync_paused`.)*
5. **InfraDbToArangoDb:** Stap 4 — Arango-sync onafhankelijke service + reporter (in plaats van gesynchroniseerde `run_arango_sync()`).
6. **AWVInfraPostGISSyncer:** Stap 7 — sync leest `pipeline_state` fase; pauwstrext maximaal 4u; autonome hervatting.
7. **RSA:** T3 — preconditions wachten (na Stap 8/7 klaar). Timeout + fallback op time-window.
8. **RSA:** T4 — sub-status/robuuste errors (incrementeel, achteraf).
9. **Alle partijen:** T5 — tests + lint.

## Configuratie-overeenkomsten

- **SQLite-locatie (`health.db`):** RSA_Health main.py:5 — zijde van repo, niet configureerbaar via `config.toml`. Akkoord per plan (single source of truth in RSA_Health).
- **API base URL:** RSA leest `pipeline_status.base_url` (T1). Dev = `http://localhost:8000`; prod = `http://127.0.0.1:8000` of via systemd `Environment=PIPELINE_STATUS_BASE_URL=...`.
- **Timeout-waarden:** T1 `pipeline_status.wait_timeout_seconds`; RSA_Health orchestrator T1/T2/T3 (T1 ~geen timeout, T2 ~10 min, T3 ~3 uur, autonome hervatting ~4 uur) — vastleggen in `RSA_Health/config.example.toml` als `timeouts {}`.
- **Power-Automate markers:** `PipelineStatus/`-map op Google Drive; naamconventie `YYYY-MM-DD_<phase>.<outcome>`. RSA_Health polled (configueerbare map via `config.toml`).

## Testen & verificatie

- `uv run python -m pytest` (Zie `pyproject.toml` → `[tool.pytest.ini_options]`, testpaths=`UnitTests`). Het project kent geen expliciet geconfigureerde linter/type-checker (alleen `pytest` in dev-deps); houd commits consistent met de bestaande stijl (type hints in `pipeline_status.py`/`ReportLoopRunner.py`/`main.py`).
- Manueel in dev: start RSA_Health (`uv run uvicorn main:app --port 8000`), start RSA `main.py`, bevestig:
  - `GET /pipeline/state` → `phase=rsa_queries, status=running`
  - `GET /pipeline/state` → `phase=rsa_queries, status=completed`
  - `GET /pipeline/state` → `phase=drive_download, status=completed` (na T2)
- Health-dashboard → “Pipeline Status” kaart update realtime.

## Risico’s & open vragen

- **Coupling tijdens transitie:** Vóór de orchestrator volledig operationeel is, valt `drive_download`/`completed` + `postgis_sync_paused` nog niet altijd binnen (RSA wacht dan vast). Mitigatie: time-based fallback (T3) + max-wait timeout → `aborted`.
- **`run_arango_sync()` in RSA_Health main.py** is synoniem met het oude model en wordt niet gebruikt door de signal-based flow; verwijderen of vrijgeven aan `InfraDbToArangoDb` als zelfstandige reporter? → **beslissing**: de functie laten bestaan als handmatige fallback, maar de onafhankelijke reporter (Stap 4) als primaire pad.
- **Gezamenlijk `pipeline_state` reset** om middernacht: moet de **orchestrator** (RSA_Health) overwegen, _niet_ RSA. RSA rappelleert nooit reset.
- **Marker-bestandscleanup Power Automate:** optioneel onderhoudsscript (>30 dagen) — nice-to-have, niet kritisch.

## Conclusie

De meeste structuur (SQLite-tabel, endpoints, health-dashboard) is in RSA_Health al aanwezig. Voor de RSA-repo zijn de minimale, concreet uitvoerbare taken **T1/T2/T3/T5**. De kritieke blokkers voor T3 zijn Stap 7 (PostGIS) en Stap 8 + Stap 6 (orchestrator + markers) in RSA_Health. Implementeer in de voornoemde volgorde; begin met T1 (config) en T2 (drive-fases rapporteren) in deze repo.
