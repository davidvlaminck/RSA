from DQReport import DQReport

r = DQReport(name='report0027',
             title='Objecten zonder relaties en geometrie',
             spreadsheet_id='1LVs9xrCLKOya5FU3GdF1DPRTEzEtDkRskOp5vkIg130',
             datasource='Neo4J',
             persistent_column='E')

# query that fetches uuids of results
result_query = """MATCH (o:onderdeel {isActief:TRUE})
WHERE NOT EXISTS ((o)--(:Asset {isActief:TRUE})) AND (o.geometry = '' OR o.geometry IS NULL)
WITH o
OPTIONAL MATCH (o:onderdeel {isActief:TRUE})-[r:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
RETURN o.uuid, o.naam, o.typeURI, a.naam as toezichter"""

r.result_query = result_query
r.run_report()


