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
- `OTLCursorPool`: singleton helper die op aanvraag de meest recente OTL SQLite-database ophaalt en read-only sqlite3 connections/cursors levert.

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

4) OTLCursorPool
- Class: `OTLCursorPool`
- Doel: Levert read-only sqlite3 connections/cursors voor de meest recente OTL SQLite-database.
- Gebruik:
  - Singleton patroon; gebruik `OTLCursorPool.get_instance()` om de instantie te verkrijgen.
  - Roep `cursor = OTLCursorPool().get_cursor()` aan om een cursor te krijgen.
- Onderhoud:
  - Zorg dat de OTL database up-to-date is; de cursor pool haalt altijd de meest recente versie op.
  - Bij wijzigingen in de database structuur, controleer of de cursor aanroep compatibel is.

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
- `OTLCursorPool`:
  - Singleton gebruik via `OTLCursorPool.get_instance()`.
  - Cursor verkrijgen met `OTLCursorPool().get_cursor()`.


## Huidige werkwijze: rapporten als Python-klassen (in `Reports/`)

De codebase gebruikt een dynamische benadering waarbij elk rapport in de map `Reports/` een Python-bestand bevat dat één (of meerdere) rapportklassen exposeert. De centrale runner (`ReportLoopRunner` / `SingleReportLoopRunner`) laadt deze bestanden on-the-fly in en voert ze uit volgens een eenvoudig contract.

Belangrijkste onderdelen en flow

- Locatie en naamconventie:
  - Rapportbestanden staan in de directory `Reports/` en hebben bestandsnamen zoals `Report0002.py`.
  - De verwachte klasse binnen het bestand heeft doorgaans exact dezelfde naam als het bestand (bijv. `Report0002`).

- Dynamische module- en klasse-loading:
  - `ReportLoopRunner.dynamic_create_instance_from_name(report_name)` gebruikt `importlib.util.find_spec(f"Reports.{report_name}")` en `importlib.util.module_from_spec()` gevolgd door `module_spec.loader.exec_module(module)` om het module-artefact in te laden en te initialiseren.
  - Vervolgens wordt de klasse opgehaald met `getattr(module, report_name)` en een instantie gemaakt.

- Contract / verwachte API van een rapportklasse:
  - `init_report(self)`: moet in de instantie aanwezig zijn en zorgen dat `self.report` aanwezig en geconfigureerd is (meestal een `DQReport` of `LegacyReport`-object). In deze methode worden queries idealiter geladen en eventuele report-specifieke initialisaties uitgevoerd.
  - `run_report(self, sender)`: wordt door de runner aangeroepen; binnen deze methode wordt doorgaans `self.report.run_report(sender=sender)` aangeroepen zodat de gedeelde logica in `DQReport`/`LegacyReport` gebruikt wordt.
  - Optioneel extra methoden of attributen mogen beschikbaar zijn, maar `init_report` en `run_report` vormen de minimale vereisten.

- Wanneer en hoe de runner bestanden detecteert:
  - De runner leest periodiek (per run) de inhoud van de `Reports/` directory (`os.listdir(self.dir_path)`) en neemt bestanden met `.py` extensie als kandidaat-rapporten.
  - Omdat de runner de directory op elk loop-interval opnieuw uitleest, kunnen nieuwe rapportbestanden worden toegevoegd zonder de runner te herstarten: het systeem ondersteunt dus "hot-add" van rapporten.

Voordelen van dit patroon

- Hot-add: nieuwe rapporten kunnen op disk worden geplaatst en worden automatisch meegenomen in de volgende run zonder herstart van de service.
- Flexibiliteit: rapporten zijn volledige Python-classes. Ze mogen complexe initialisatie en custom logica bevatten, andere classes gebruiken of helper-functies aanroepen.
- Eenvoudige conventie: bestandsnaam == klasse-naam is voorspelbaar en maakt dynamische loading simpel.

Aandachtspunten en best practices

- `init_report()` gebruiken voor setup en het inladen van queries
  - Leg querystrings en configuratie in `init_report()` (in plaats van globaal in het module) zodat herladen of meerdere instanties voorspelbaar werkt.

- Minimaliseer module-global state
  - Globale variabelen in report-modules kunnen leiden tot onverwacht gedrag bij meerdere loads of bij herladen. Initialisatie en mutatie horen binnen `init_report()` of in objecten plaats te vinden.

- Namen en zichtbaarheid
  - Houd de klasse-naam en bestandsnaam synchroon (zoals nu de conventie is). Als je meerdere classes wil aanbieden in één bestand, zorg dan dat de runner de juiste klasse kan vinden (de huidige runner verwacht dezelfde naam als bestand).

- Fouten en isolatie
  - `ReportLoopRunner.run()` vangt exceptions per rapport af en logt ze (zodat één fout een volgende rapportuitvoering niet blokkeert). Zorg ervoor dat `run_report` exceptions op een zinvolle manier afhandelt of laat ze bubbelen zodat de runner ze kan loggen.

- Resource- en connector-initialisatie
  - Connectoren (Singletons zoals `SinglePostGISConnector`, `SingleNeo4JConnector`, `SingleArangoConnector`, en `SingleSheetsWrapper`) worden in de runner éénmaal geïnitialiseerd en gedeeld met de rapporten. Rapporten moeten deze singletons via hun normale API gebruiken (bijv. `SinglePostGISConnector.get_connector()`), of de `factories.make_datasource()` route voor DQReport.

- Performance en blocking
  - De runner voert rapporten sequentieel uit in dezelfde thread / proces. Als een rapport lang loopt, vertraagt dat de rest. Overweeg future work: parallelisatie per rapport (met limiet), timeouts per rapport, of subprocess-isolatie voor zware rapporten.

- Caching en imports
  - De huidige loader maakt een nieuw module-object en voert `exec_module()`. Dit betekent dat code die bij import zware initialisatie doet kan worden uitgevoerd telkens wanneer een module geladen wordt. Houd daar rekening mee.

Korte richtlijn / template voor nieuwe rapporten

- Bestandsnaam: `Reports/ReportXXXX.py`
- Klasse (minimaal):

```python
from lib.reports.DQReport import DQReport

class ReportXXXX:
    def init_report(self):
        self.report = DQReport(name='reportXXXX', title='...', spreadsheet_id='...', datasource='ArangoDB')
        # zet hier self.report.result_query = '...' of laad query uit bestand

    def run_report(self, sender):
        self.report.run_report(sender=sender)
```

- Plaats complexe of gedeelde helpercode in `lib/` (bijv. `lib/reports/` of `lib/connectors/`) in plaats van per-rapport-modules.


---

Einde van de documentatie-sectie over de huidige werkwijze.
