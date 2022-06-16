from DQReport import DQReport


r = DQReport(name='report0030',
             title='Netwerkelementen hebben een (afgeleide) locatie',
             spreadsheet_id='1ZAZ8chzMbLEyGd-cbZM6S7Uw4aNOrBmAE1KWnbyvdK4',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkelement {isActief:TRUE})
WHERE n.geometry IS NULL
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()
