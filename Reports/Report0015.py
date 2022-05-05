from DQReport import DQReport


r = DQReport(name='report0015',
             title='Camera\'s hebben een unieke naam',
             spreadsheet_id='1GM6mBwfsLkEELjroSw-df6A2HXSQnOFAeudUzTybMQE',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Camera {isActief:TRUE})
WITH a.naam AS naam, COUNT(a.naam) AS aantal
WHERE aantal > 1
MATCH (b:Camera {isActief:TRUE, naam:naam})
RETURN b.uuid, b.naam"""

r.result_query = result_query
r.run_report()
    

