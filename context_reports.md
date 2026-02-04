# Overzicht: soorten rapporten en hun structuur

Kort plan

- Lees de belangrijkste rapport-implementaties (`Report`, `DQReport`, `LegacyReport`, `LegacyHistoryReport`, `KladRapport`).
- Beschrijf de soorten rapporten en hoe ze werken (levenscyclus, velden, outputs).
- Geef concrete refactor- en onderhoudsaanwijzingen gebaseerd op de code.

Doel

Dit document beschrijft de soorten rapporten in de codebase en legt uit welke verwachtingen en conventies de rapport-implementaties (basis en derivaten) gebruiken. Gebruik dit als referentie bij refactorings en bij het toevoegen van nieuwe rapporten.

Belangrijke classes / scripts

- `Report` (basis): minimale container voor metadata: `name`, `title`, `spreadsheet_id`, `datasource`, `result_query`, `add_filter`, `frequency`, `summary_sheet_id`.
- `DQReport` (de moderne rapport-implementatie): afgeleid van `Report`, generieke uitvoer- en datasource-abstracties met Google Sheets-output en e-mail notificatie.
- `LegacyReport`: oudere, meer directe implementatie voor Neo4j/PostGIS-queries; bouwt resultaatsets als lijsten en schrijft direct naar een opgegeven sheet.
- `LegacyHistoryReport`: variant van `LegacyReport` die per run een nieuw tabblad (historiek) aanmaakt en historiek en samenvatting bijhoudt.
- `KladRapport.py`: een klein runnable script dat met `DQReport` (of andere report-klasse) een test-run opstart; gebruikt lokale connectorinitialisatie (o.a. Neo4j, Sheets).

Hoofdtypen rapporten (op basis van implementatie)

1) DQ-rapporten
- Class: `DQReport`
- Datasources: adapters via `factories.make_datasource()` (PostGIS, ArangoDB, mogelijk Neo4j)
- Kenmerken:
  - Gebruikt een datasource-adapter `ds` en output-adapter `out`.
  - Roept `ds.test_connection()` aan vóór uitvoering.
  - Verwacht `ds.execute(query)` te retourneren in een `QueryResult`-achtig object met velden: `rows`, `keys`, `query_time_seconds`, `last_data_update`.
  - Schrijft resultaten via `out.write_report(ctx, qr, ...)` (OutputWriteContext).
  - Houdt historiek bij in tabblad `Historiek` en update samenvattingsblad (`Overzicht`).
  - Ondersteunt een optionele `persistent_column`-mechaniek (behoud van opmerkingen per rij).
- Typische use-cases: graf- en relationele queries, Google Sheets-output, automatische notificaties.

2) Legacy-rapporten
- Classes: `LegacyReport`, `LegacyHistoryReport`
- Datasources: direct gebruik van connectoren (`SingleNeo4JConnector`, `SinglePostGISConnector`).
- Kenmerken:
  - Directe SQL/Neo4j-executie binnen de class (soms met connection pooling).
  - `LegacyHistoryReport` maakt per run een nieuw sheet met naam `dd/mm/YYYY` en houdt historiek en samenvattingen bij.
  - Werkt vaak op lagere niveau-API's (cursor, driver.session, etc.) en bouwt rows/headers zelf.
- Typische use-cases: oudere rapporten waarin de logica sterk geïntegreerd is met query-executie en sheet-formattering.

3) Klad / Dev-rapporten
- Script-achtige entries zoals `KladRapport.py` die lokaal connectoren initialiseren en een `DQReport` of ander rapport draaien.
- Handig voor debugging en ad-hoc runs, niet per se conform library-initialisatie-conventies.

Levenscyclus / run flow (samengevat)

1. Constructie: een `Report` object wordt geconfigureerd met metadata (`name`, `title`, `spreadsheet_id`, `datasource`, `persistent_column`, etc.).
2. Init / pre-run checks: adapters (datasource, output) worden aangemaakt via factories; connectoren worden geïnitialiseerd of geverifieerd.
3. Query-executie:
   - Bij `DQReport`: `ds.test_connection()` gevolgd door `ds.execute(self.result_query)`.
   - Bij `LegacyReport`: directe execution op connector (cursor/driver.session).
4. Post-processing:
   - Keys/headers bepalen; bij ArangoDB kan `keys` leeg zijn en wordt dit in `DQReport` afgeleid uit `rows[0]`.
   - Converteer en clean data (datetijd, Decimal -> str, lists -> pipe-delimited strings).
5. Write-out:
   - `DQReport` roept `out.write_report(...)` met een `OutputWriteContext`.
   - `LegacyReport` en `LegacyHistoryReport` schrijven rechtstreeks via `SheetsWrapper`.
6. Historiek en samenvatting bijwerken: `Historiek`-tabblad en `Overzicht` worden aangepast; query-execution time en last-data-update worden bijgehouden.
7. Mails: indien mailing ranges aanwezig, bouw en verstuur mails via `MailSender`.

Belangrijke attributen en conventies

- `datasource`: string die bepaalt welke datasource-factory wordt gebruikt (voor `DQReport` via `factories.make_datasource`).
- `result_query`: de querystring die uitgevoerd wordt; in `DQReport` kan dit AQL of SQL zijn, afhankelijk van `datasource`.
- `persistent_column`: optioneel, kolomletter (bijv. 'C') gebruikt om blijvende opmerkingen te bewaren. Wordt door `DQReport` en history-variant gelezen en toegepast.
- `summary_sheet_id`, `Historiek`, `Resultaat` en `Overzicht`: conventionele sheetnamen/locaties die de code gebruikt om overzicht en historiek te bewaren.

Wat je terugvindt in de code (praktische herkenningspunten)

- `DQReport`:
  - Roept `make_datasource(self.datasource)` en `make_output(self.output)` aan.
  - Verwacht `qr = ds.execute(self.result_query)` en `qr` heeft `rows` + optioneel `keys`, `query_time_seconds`, `last_data_update`.
  - Bij ArangoDB: als `qr.keys` leeg is en `qr.rows` dicts bevat, maakt `DQReport` een nieuw `QueryResult`-object aan met afgeleide keys.
- `LegacyReport` / `LegacyHistoryReport`:
  - Gebruiken `SingleNeo4JConnector.get_connector()` of `SinglePostGISConnector.get_connector()`.
  - Bouwen headers (`result_keys`) en rows zelf; converteren `decimal.Decimal` naar `str`.
  - `LegacyHistoryReport` voegt extra logica voor sheet-rolling en persistent column.
- `KladRapport.py`:
  - Voorbeelden van hoe je connectors initieert en `DQReport` configureert voor een ad-hoc run.
