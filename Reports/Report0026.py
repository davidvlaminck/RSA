from DQReport import DQReport


r = DQReport(name='report0026',
             title='Paden hebben een HoortBij relatie naar Zpad objecten',
             spreadsheet_id='18KfmYhpxc75ECyN54WFtKrG4Hdz6GPCXzH5i8Zi0144',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset:Pad {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:HoortBij]->(:Asset:Zpad {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()


