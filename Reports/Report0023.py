from DQReport import DQReport


r = DQReport(name='report0023',
             title='Camera\'s hebben een toezichter',
             spreadsheet_id='1p5njgNTQ3G4aogAjb2sdJTvxzXgI2z-Cd6iqlla5L0c',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (c:Camera {isActief:TRUE})
WHERE NOT EXISTS ((c)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))
RETURN c.uuid, c.naam"""

r.result_query = result_query
r.run_report()


