from DQReport import DQReport


r = DQReport(name='report0003',
             title='Verkeersregelaars hebben een Bevestiging relatie naar een Wegkantkast',
             spreadsheet_id='1tud5st23sWAKYxdtGUmNHS1Tt54GW31HwkJPaXYXrtE',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset :Verkeersregelaar {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:Bevestiging]-(:Wegkantkast {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()
    

