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
- `scripts/ops/drive_sync_gate.py` → `DailyDriveSyncGate.ensure_synced` rapporteert `drive_download` running/completed/failed en wacht op orchestrator-signaal `drive_download/starting`; `upload_after_run` rapporteert `drive_upload` running/completed/failed en wacht op `drive_upload/starting`. → **T2 gereed**
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

- `scripts/ops/drive_sync_gate.py:32-43` — `DailyDriveSyncGate.ensure_synced` wacht eerst tot `pipeline_state` = `drive_download / starting` (gezet door orchestrator). Zodra dat signaal komt, start de sync, wordt fase -> `running` gezet, en na afronding -> `completed` of `failed`.
- `scripts/ops/drive_sync_gate.py:68-84` — `upload_after_run` wacht tot `pipeline_state` = `drive_upload / starting`. Bij timeout (30 min) wordt de upload toch gestart. Fase -> `running` tijdens upload, -> `completed` of `failed` na afronding.

### T3 — RSA wacht op preconditions vóór rapportage start

**Status: ✓ Gereed**

- `ReportLoopRunner.start()` (signal-based mode): leest `pipeline_state.get()` en wacht tot `drive_download = completed` én `postgis_sync` in `paused / running / resuming` is.
- Timeout via `pipeline_state.wait_timeout_seconds` (default 7200s). Bij timeout: rapporteer `rsa_queries / aborted` en overslaan van de rest van de dag.
- Idempotentie: alleen rapporteren wanneer de fase zich daadwerkelijk wijzigt (via `pipeline_status.update()` in `run()`).

### T4 — RSA rapporteert fase-overgangen en fouten robuust

**Status: ✓ Gereed**

- Bestaande `rsa_queries` reporting in `run()` blijft; `failed` incl. exception-message (`str(exc)`).
- Finer-grained sub-statussen via `message`-veld:
  - Sequentieel: `_run_sequential` update `message` met `Verwerken: ReportName (idx/totaal)` vóór elk rapport.
  - Parallel: `_run_parallel_by_datasource` update `message` met `Parallel: N rapporten, poging X/Y`.
- Geen nieuwe fasen nodig; `phase` blijft `rsa_queries`, enkel `message` verrijkt.

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
| 5 | RSA rapporteert `rsa_queries` + drive-phases, wacht op preconditions, sub-statussen | ~ (reporting ✓; drive-phases met signal-gating ✓; preconditions ✓; sub-statussen ✓) | RSA (T5) |
| 6 | Power-Automate via Drive marker-bestanden | ✗ (detectie ontbreekt) | RSA_Health (marker polling) + Power Automate |
| 7 | PostGIS sync pauzeren/hervatten via `pipeline_state` | ✗ (sync script leest fase) | AWVInfraPostGISSyncer |
| 8 | Achtergrond-orchestrator (drive-steps, sequencing, reset, markers) | ✗ | RSA_Health |
| +midnight | Dagelijkse reset om middernacht | ✗ | RSA_Health |

## Implementatievolgorde (prioriteit)

Gewicht: prioriteit binnen deze repo (RSA) eerst, rest als afhankelijkheid/blok.

1. **RSA:** T5 — tests + lint.
3. **RSA_Health:** Stap 8/6 — orchestrator + Power-Automate marker polling.
4. **RSA_Health:** Stap 7 — PostGIS pause/resume endpoint/signaling.
5. **InfraDbToArangoDb:** Stap 4 — Arango-sync onafhankelijke service + reporter.
6. **AWVInfraPostGISSyncer:** Stap 7 — sync leest `pipeline_state` fase; pauzeert maximaal 4u; autonome hervatting.

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

T1 (config), T2 (drive-phases rapporteren met orchestrator-signaal-gating), T3 (precondition-gating met timeout) en T4 (sub-statussen via `message`-veld) zijn reeds geïmplementeerd in deze repo via directe SQLite-toegang in plaats van het oorspronkelijk geplande HTTP-model. De enige open RSA-taak is T5 (tests). De overige Stappen in RSA_Health (6/7/8) respectievelijk InfraDbToArangoDb (4) en AWVInfraPostGISSyncer (7) zijn nog in uitvoering.
