from DQReport import DQReport


r = DQReport(name='report0002',
             title='TLCfipoorten hebben een sturingsrelatie naar een Verkeersregelaar',
             spreadsheet_id='1C4OvyX6uQfe3eKa8A_ClsTfnmAcBy-45Q-18htdxHHM',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset :TLCfiPoort {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:Sturing]-(:Verkeersregelaar {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()
    

