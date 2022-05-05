from DQReport import DQReport


r = DQReport(name='report0004',
             title='Verkeersregelaars hebben een unieke naam',
             spreadsheet_id='1aGZFPAeFgkQgU2XcrKhVKK1NPu-OEPuskPvWsnAyEYU',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
WITH a.naam AS naam, COUNT(a.naam) AS aantal
WHERE aantal > 1
MATCH (b:Verkeersregelaar {isActief:TRUE, naam:naam})
RETURN b.uuid, b.naam"""

r.result_query = result_query
r.run_report()
    

