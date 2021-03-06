from DQReport import DQReport


r = DQReport(name='report0032',
             title="Netwerkpoorten hebben een type",
             spreadsheet_id='1CNSGgZbARVwRzrMB5a2LrSz-HJblvzAGWODsPOFE1jo',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})-[:Bevestiging]-(e:Netwerkelement {isActief:TRUE})
WHERE NOT e.merk IN ['NOKIA', 'Ciena']
WITH n
WHERE n.type IS NULL 
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()
