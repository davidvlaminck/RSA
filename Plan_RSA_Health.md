# Plan RSA_Health — Signal-based Pipeline Orchestrator

Verplicht van `RSA_Health/orchestrator.md` (signal-based, SQLite-driven pipeline).
Dit plan legt uit welke zaken al geïmplementeerd zijn, wat nog mist, en hoe dat hier (in deze repo **RSA**) én in de bijbehorende repos afgestemd wordt.

## Scope & verantwoording

`orchestrator.md` beschrijft een pipeline die zich over meerdere onafhankelijke services verspreidt. De centrale bron van waarheid (`pipeline_state` in SQLite) en de FastAPI-orchestrator leven in **RSA_Health**; de **RSA**-reportservice rapporteert hieraan. Dit plan volgt die scheidingslijn:

| Component | Repo | Eigenaar plan |
|---|---|---|
| FastAPI server (`/pipeline/update`, `/pipeline/state`, `/health`, `/history`), `pipeline_state`-tabel, health-dashboard | `RSA_Health` | RSA_Health |
| Achtergrond-orchestrator (drive-steps, sequencing, midnight-reset, Power-Automate markers) | `RSA_Health` | RSA_Health |
| PostgreSQL pause/resume van `AWVInfraPostGISSyncer` | `AWVInfraPostGISSyncer` | AWVInfraPostGISSyncer (extern) |
| Arango-sync (rapporteert `arango_sync`) | `InfraDbToArangoDb` | InfraDbToArangoDb (extern) |
| RSA-reportservice: rapporteert `rsa_queries`, respecteert preconditions | `RSA` (deze repo) | RSA |
| Power Automate (SharePoint↔Drive marker-bestanden) | extern (Microsoft) → via Drive | Power Automate |

> Dit plan wordt in de **RSA**-repo vertrokken, maar benoemt alle owners. De RSA-specifieke taken staan in §3 (RSA-taken) en worden in de implementatievolgorde in §4 gehonoreerd.

## Huidige stand van implementatie (audited 2026-08-03)

### RSA (deze repo) — RSA-queries-service

- `lib/connectors/pipeline_state.py` → `PipelineState` schrijft direct naar SQLite (`health.db`), tabel `pipeline_state`. Geen HTTP API meer. Dit is de geëvolueerde implementatie van het oorspronkelijk geplande HTTP-based `PipelineStatusReporter`-model.
- `lib/reports/ReportLoopRunner.py` (`run()`, ~244:261) rapporteert `rsa_queries` running/completed/failed via `self.pipeline_status` (een `PipelineState`-instantie). → **Stap 5 gedeeltelijk ✓**
- `scripts/ops/drive_sync_gate.py` → `DailyDriveSyncGate.ensure_synced` rapporteert `drive_download` running/completed/failed; `upload_after_run` rapporteert `drive_upload` running/completed/failed. Beide via directe `PipelineState.update()` calls. → **Stap 5T2 gereed**
- `settings_sample.json` + `settings_parallel_example.json` bevatten een `pipeline_state`-blok met `enabled` + `db_path`. → **Stap 5T1 gereed**
- Nog niet geïmplementeerd:
  - Geen precondition-gating voor `drive_download=completed` + `postgis_sync=paused` voor `rsa_queries` start. → **T3 open**
  - Geen per-datasource sub-statussen. → **T4 open**
  - Geen tests voor `PipelineState`, `DailyDriveSyncGate`, of `upload_after_run` pipeline-transities. → **T5 open**

## RSA-taken (wat deze repo moet doen)

Deze taken zijn de verantwoordelijkheid van de RSA-repo en vormen de minimale invulling van stap 5 + de integrationspunten voor de orchestrator.

### T1 — `pipeline_state`-config in settings

**Status: ✓ Gereed**

- `settings_sample.json` + `settings_parallel_example.json`: blok `pipeline_state` { `enabled`, `db_path` }.
- `ReportLoopRunner.__init__` leest het blok en instantieert `PipelineState(db_path)` indien ingeschakeld. → `lib/reports/ReportLoopRunner.py:140-146`
- `main.py` leest hetzelfde blok en geeft de instantie door aan `DailyDriveSyncGate` en `upload_after_run`. → `main.py:117-125`

### T2 — RSA rapporteert drive-phases aan de orchestrator

**Status: ✓ Gereed**

- `scripts/ops/drive_sync_gate.py:42` — `drive_download/running` bij start sync.
- `scripts/ops/drive_sync_gate.py:59` — `drive_download/completed` bij succes; `drive_download/failed` bij falen of invalid mirror.
- `scripts/ops/drive_sync_gate.py:70` — `drive_upload/running` bij start upload.
- `scripts/ops/drive_sync_gate.py:80` — `drive_upload/completed` bij succes; `drive_upload/failed` bij falen.

### T3 — RSA wacht op preconditions vóór rapportage start

**Status: Open**

- RSA moet wachten tot `drive_download = completed` **en** `postgis_sync = paused` (of `postgis_sync_running` buiten de pauze-periode) is, vóór `rsa_queries` start.
- Huidige `_is_within_run_window(05:00–23:59)` in `ReportLoopRunner` blijft als **time-based fallback**, maar signal-based gating heeft voorrang.
- Implementatie-optie: `ReportLoopRunner` leest `PipelineState.get()` vóór `run()`. Wacht met timeout (bijv. `pipeline_state.wait_timeout_seconds`, default 7200s) en rapporteer `aborted` bij expiry.
- Idempotentie: alleen rapporteren wanneer de fase zich daadwerkelijk wijzigt.

### T4 — RSA rapporteert fase-overgangen en fouten robuust

**Status: Open**

- Bestaande `rsa_queries` reporting in `run()` blijft; zorg dat `failed` incl. exception-message wordt gemeld (reeds zo, `str(exc)`).
- Voeg optionele finer-grained sub-statussen toe (bv. per datasource) via `message`-veld, zonder nieuwe fasen.

### T5 — Tests

**Status: Open**

- `UnitTests/` → test `PipelineState.update/get` met een in-memory SQLite db (verifieer fase-transities).
- Test `DailyDriveSyncGate.ensure_synced` + `upload_after_run` integratie met een stub `PipelineState` om fase-transitie calls te assert-en.
- Test `ReportLoopRunner.run()` precondition-wait (mock `PipelineState.get()`).

## Stappen uit `orchestrator.md` → status & owner

| Stap | Omschrijving | Status | Owner |
|---|---|---|---|
| 1 | SQLite `pipeline_state`-tabel + seed | ✓ | RSA_Health |
| 2 | `POST /pipeline/update` + `GET /pipeline/state` | ✓ | RSA_Health |
| 3 | Health-pagina polling van fase/status | ✓ | RSA_Health |
| 4 | Arango-sync rapporteert `arango_sync` | ~ (sync functie bestaat; moet onafh. service + reporter worden) | InfraDbToArangoDb |
| 5 | RSA rapporteert `rsa_queries` + drive-phases, wacht op preconditions | ~ (reporting ✓; drive-phases ✓; preconditions ✗) | RSA (T3/T4) |
| 6 | Power-Automate via Drive marker-bestanden | ✗ (detectie ontbreekt) | RSA_Health (marker polling) + Power Automate |
| 7 | PostGIS sync pauzeren/hervatten via `pipeline_state` | ✗ (sync script leest fase) | AWVInfraPostGISSyncer |
| 8 | Achtergrond-orchestrator (drive-steps, sequencing, reset, markers) | ✗ | RSA_Health |
| +midnight | Dagelijkse reset om middernacht | ✗ | RSA_Health |

## Implementatievolgorde (prioriteit)

Gewicht: prioriteit binnen deze repo (RSA) eerst, rest als afhankelijkheid/blok.

1. **RSA:** T3 — preconditions wachten (na Stap 8/6/7 klaar in RSA_Health). Timeout + fallback op time-window.
2. **RSA:** T4 — sub-status/robuuste errors (incrementeel, achteraf).
3. **RSA:** T5 — tests + lint.
4. **RSA_Health:** Stap 8/6 — orchestrator + Power-Automate marker polling. *(Blok voor RSA T3, want `drive_download`/`completed` en `postgis_sync`/`paused` komen uit de orchestrator of externe signalen.)*
5. **RSA_Health:** Stap 7 — PostGIS pause/resume endpoint/signaling. *(Blok voor RSA T3 precondition `postgis_sync_paused`.)*
6. **InfraDbToArangoDb:** Stap 4 — Arango-sync onafhankelijke service + reporter.
7. **AWVInfraPostGISSyncer:** Stap 7 — sync leest `pipeline_state` fase; pauzeert maximaal 4u; autonome hervatting.

## Configuratie-overeenkomsten

- **SQLite-locatie (`health.db`):** RSA_Health bepaalt de locatie; RSA leest `pipeline_state.db_path` uit eigen settings. Akkoord per plan (single source of truth in RSA_Health).
- **Geen HTTP base_url meer:** De oorspronkelijk geplande `pipeline_status.base_url` is vervangen door directe SQLite-toegang via `pipeline_state.db_path`. Er zijn geen HTTP-calls meer vanuit RSA naar RSA_Health voor pipeline-status.
- **Timeout-waarden:** Indien T3 een `wait_timeout_seconds` introduceert, wordt die in RSA geregistreerd. De orchestrator-timeouts (arango ~4h, postgis-pauze ~10min, rsa ~3u) blijven in RSA_Health.
- **Power-Automate markers:** `PipelineStatus/`-map op Google Drive; naamconventie `YYYY-MM-DD_<phase>.<outcome>`. Detectie in RSA_Health (configueerbare map via `config.toml`).

## Testen & verificatie

- `uv run python -m pytest` (Zie `pyproject.toml` → `[tool.pytest.ini_options]`, testpaths=`UnitTests`).
- Manueel in dev: start RSA_Health, start RSA `main.py`, bevestig:
  - `GET /pipeline/state` → `phase=drive_download, status=completed` (na sync)
  - `GET /pipeline/state` → `phase=rsa_queries, status=running`
  - `GET /pipeline/state` → `phase=rsa_queries, status=completed`
- Health-dashboard → “Pipeline Status” kaart update realtime.

## Risico’s & open vragen

- **Coupling tijdens transitie:** Vóór de orchestrator volledig operationeel is, valt `drive_download`/`completed` + `postgis_sync_paused` nog niet altijd binnen (RSA wacht dan vast). Mitigatie: time-based fallback (T3) + max-wait timeout → `aborted`.
- **Gezamenlijk `pipeline_state` reset** om middernacht: moet de **orchestrator** (RSA_Health) overwegen, _niet_ RSA. RSA rappelleert nooit reset.
- **Marker-bestandscleanup Power Automate:** optioneel onderhoudsscript (>30 dagen) — nice-to-have, niet kritisch.

## Conclusie

T1 (config) en T2 (drive-phases rapporteren) zijn reeds geïmplementeerd in deze repo, maar via directe SQLite-toegang in plaats van het oorspronkelijk geplande HTTP-model. De overige RSA-taken (T3 preconditions, T4 robuustheid, T5 tests) zijn open en wachten op de voltooiing van Stap 6/7/8 in RSA_Health respectievelijk Stap 4 in InfraDbToArangoDb. Implementeer T3 eerst; T4 en T5 zijn daarna incrementeel uit te voeren.
