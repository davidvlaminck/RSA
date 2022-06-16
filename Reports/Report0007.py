from DQReport import DQReport


r = DQReport(name='report0007',
             title='Camera\'s hebben een Sturing relatie met een Netwerkpoort of Omvormer',
             spreadsheet_id='1NKB8J6is9xTrIrDcZAP_IraBqs65JhTpoCLDMaT881A',
             datasource='Neo4J',
             persistent_column='D')

# query that fetches uuids of results
result_query = """MATCH (c:Camera {isActief:TRUE}) 
WHERE NOT EXISTS ((c)-[:Sturing]-(:onderdeel :Netwerkpoort {isActief:TRUE})) AND NOT EXISTS ((c)-[:Sturing]-(:onderdeel :Omvormer {isActief:TRUE}))
WITH c
OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
RETURN c.uuid, c.naam, a.naam as toezichter"""

r.result_query = result_query
r.run_report()


