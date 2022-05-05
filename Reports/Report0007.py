from DQReport import DQReport


r = DQReport(name='report0007',
             title='Camera\'s hebben een Sturing relatie met een Netwerkpoort of Omvormer',
             spreadsheet_id='1NKB8J6is9xTrIrDcZAP_IraBqs65JhTpoCLDMaT881A',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset :onderdeel :Camera {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:Sturing]-(:onderdeel :Netwerkpoort {isActief:TRUE})) AND NOT EXISTS ((a)-[:Sturing]-(:onderdeel :Omvormer {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()


