from DQReport import DQReport


r = DQReport(name='report0017',
             title='Netwerkkaarten hebben een Bevestiging relatie met een Netwerkelement',
             spreadsheet_id='1UfYhxcM0z8uq9-GwfDJhHNVpuhoWtUprrPGMfPSXeGk',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkkaart {isActief:TRUE})
WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkelement {isActief:TRUE}))
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()


