from DQReport import DQReport

r = DQReport(name='report0028',
             title='IP Netwerkelementen (niet merk Nokia of Ciena) hebben een HoortBij relatie met een legacy object van type IP',
             spreadsheet_id='1wn05XDV1PkyVdGgDEO3yUU0Jqf3t6asGH0SyGXQQWS8',
             datasource='Neo4J',
             persistent_column='G')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (n:Netwerkelement {isActief:TRUE})-[h:HoortBij]->(i:installatie {isActief:TRUE})
WHERE (NOT n.merk IN ['NOKIA', 'Ciena'] AND (h IS NULL OR (NOT(i:IP) AND i.typeURI CONTAINS 'lgc')))
RETURN n.uuid, n.naam, n.merk, i.uuid as installatie_uuid, i.naampad as installatie_naampad, i.typeURI"""

r.result_query = result_query
r.run_report()


