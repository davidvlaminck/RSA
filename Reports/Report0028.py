from DQReport import DQReport

r = DQReport(name='report0028',
             title='IP Netwerkelementen (niet merk Nokia of Ciena) hebben een HoortBij relatie met een legacy object van type IP',
             spreadsheet_id='1wn05XDV1PkyVdGgDEO3yUU0Jqf3t6asGH0SyGXQQWS8',
             datasource='Neo4J',
             persistent_column='G')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkelement {isActief:TRUE})
WHERE NOT n.merk IN ['NOKIA', 'Ciena'] AND NOT EXISTS ((n)-[:HoortBij]->(:IP {isActief:TRUE}))
RETURN n.uuid, n.naam, n.merk"""

r.result_query = result_query
r.run_report()


