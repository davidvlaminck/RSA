from DQReport import DQReport


r = DQReport(name='report0029',
             title='IP elementen hebben HoortBij relatie met een Netwerkelement',
             spreadsheet_id='1VJmqHesEfOaZzYD8rZdZUNeKUoCBKMetgltL74bX9jk',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (c:Camera {isActief:TRUE})
WHERE NOT EXISTS((c)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))
RETURN c.uuid, c.naam"""

r.result_query = result_query
r.run_report()
