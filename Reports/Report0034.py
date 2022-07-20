from DQReport import DQReport


r = DQReport(name='report0034',
             title="NNI Netwerkpoorten hebben een Sturing relatie met een NNI Netwerkpoort",
             spreadsheet_id='1Q0ypijGhIMmax4iR3DHHu4FMYVbkU_LCQhBAyzbIA2k',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})
WHERE NOT EXISTS ((n)-[:Sturing]->(:Netwerkpoort {isActief:TRUE, type:'NNI'}))
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()
