from DQReport import DQReport


r = DQReport(name='report0023',
             title='Camera\'s hebben een toezichter',
             spreadsheet_id='1p5njgNTQ3G4aogAjb2sdJTvxzXgI2z-Cd6iqlla5L0c',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (c:Camera)-[h:HeeftBetrokkene {rol:'toezichter'}]->()
WHERE c IS NOT NULL AND h IS NULL
RETURN c.uuid, c.naam"""

r.result_query = result_query
r.run_report()


