from DQReport import DQReport


r = DQReport(name='report0029',
             title='IP elementen hebben een bijbehorend Netwerkelement',
             spreadsheet_id='1VJmqHesEfOaZzYD8rZdZUNeKUoCBKMetgltL74bX9jk',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (i:IP {isActief:TRUE})
WHERE NOT EXISTS((i)<-[:HoortBij]-(:Netwerkelement {isActief:TRUE}))
RETURN i.uuid, i.naam, i.naampad, i.`tz:toezichter.tz:gebruikersnaam` as toezichter"""

r.result_query = result_query
r.run_report()
