from DQReport import DQReport


r = DQReport(name='report0025',
             title='Linken hebben een HoortBij relatie naar Pad objecten',
             spreadsheet_id='1PwWn1E4VRsXRa8L7Lh0Pmjy1Z0ZKCoclDO0bvHx3EaY',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset :Link {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:HoortBij]->(:Pad {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()


