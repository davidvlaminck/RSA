from DQReport import DQReport


r = DQReport(name='report0033',
             title="VLAN objecten hebben een HoortBij relatie met een L2AccesStructuur",
             spreadsheet_id='12urCVlUXm_KbNCrQS1MH5kVqNKak3n5DdQlAnk8mn9w',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:VLAN {isActief:TRUE}) 
WHERE NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()
