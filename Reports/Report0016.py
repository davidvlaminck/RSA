from DQReport import DQReport


r = DQReport(name='report0016',
             title='Netwerkpoorten hebben een Bevestiging relatie met een Netwerkelement of een Netwerkkaart',
             spreadsheet_id='16NJCwhrHnYuz6Z9leqGswfOR0bt7EdBK_GonPB-3y7o',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkpoort {isActief:TRUE})
WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkkaart {isActief:TRUE})) and NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkelement {isActief:TRUE}))
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()


