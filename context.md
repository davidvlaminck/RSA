# Projectoverzicht

Deze repository is een rapporteringsservice voor de infrastructuur data van AWV. De service zet rapporten op vanuit meerdere externe databronnen die lokaal op dezelfde machine gehost worden.

Belangrijkste eigenschappen

- De service leest data uit ArangoDB en PostGIS. Historisch werd ook Neo4j gebruikt (sommige oude code en rapporten verwijzen hier nog naar).
- Rapporten worden gegenereerd door Python-scripts in de map `Reports`. Elk rapport bevat logica om data op te halen, verwerken en weg te schrijven (bijv. Google Sheets, Excel of mail).
- Na een volledige run van rapporten worden er e-mails verzonden (geschiedenis en notificaties).

Databases

- ArangoDB: gebruikt voor graph relaties (assets, assetrelaties, afgeleide edge-collecties zoals `voedt_relaties`, en bijhorende graphs). Dit is de primaire graph-datasource.
- PostGIS: relationele/spatiale database gebruikt voor queries die geografische of relationele data bevatten.
- Neo4j: historisch gebruikt; er kunnen nog referenties en oude queries aanwezig zijn maar actieve runs gebruiken ArangoDB / PostGIS.

Belangrijke mappen / bestanden

- `Reports/` — hoofdmap met alle rapportdefinities (bv. `Report0002.py`, `Report0003.py`, ...). Hier staan vaak AQL-queries of SQL-queries die de datasource aanroepen.
- `AQL/` — losse AQL-scripts en hulpmiddelen; bevat voorbeelden en ad-hoc queries die gebruikt werden om problemen te analyseren of het datamodel te begrijpen.
- `ArchivedReports/` — gearchiveerde oudere rapporten (historisch). Deze bestanden mogen worden meegerefactord, maar worden in principe niet meer actief uitgevoerd. Het is handig ze hier te bewaren voor zoekbaarheid en referentie (versus volledig verwijderen uit versiebeheer).
- `datasources/` — implementaties voor verschillende datasources (ArangoDB, PostGIS, Neo4j vroeger). Zorg dat nieuwe derived-collections en connectoren (bv. `voedt_relaties`, `voedt_graph`, `SingleArangoConnector`) correct worden aangemaakt en gebruikt door de datasource-implementatie.
- `outputs/` — schrijflaag (Google Sheets, Excel, MS Graph uploads ...).
- `run_single_report.py`, `ReportLoopRunner.py` — hulpscripts om rapporten één voor één of in een loop uit te voeren.

Opmerkingen en workflow-notities

- In `AQL/` staan nuttige voorbeelden die gebruikt kunnen worden om het graphmodel te doorgronden. Die kunnen ook dienen als basis voor geïnternaliseerde queries in `Reports/`.
- `ArchivedReports/` is primair bedoeld als doorzoekbare archive en is handiger voor snelle referentie dan enkel versiebeheer (git) — behoudt bestandsgeschiedenis en maakt het eenvoudiger om oude queries terug te vinden.
- Er bestaan afgeleide edge-collecties (bv. `voedt_relaties`, `sturing_relaties`, `bevestiging_relaties`, `hoortbij_relaties`) die alleen relaties bevatten waarvoor beide endpoints actief zijn. Deze wordt aangeraden te gebruiken in rapporten omdat traversals en detectie van loops hierdoor veel efficiënter zijn.
