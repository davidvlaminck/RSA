from DQReport import DQReport


r = DQReport(name='report0024',
             title='Netwerkelementen hebben een unieke naam',
             spreadsheet_id='1oV97_-ZrhMxHhsGkYv6vCfQLgivN8kH6BRsrveUP3yM',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Netwerkelement {isActief:TRUE})
WITH a.naam AS naam, COUNT(a.naam) AS aantal
WHERE aantal > 1
MATCH (b:Netwerkelement {isActief:TRUE, naam:naam})
RETURN b.uuid, b.naam"""

r.result_query = result_query
r.run_report()


