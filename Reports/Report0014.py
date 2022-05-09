from DQReport import DQReport


r = DQReport(name='report0013',
             title='Stroomkringen en Laagspanningsborden hebben een HoortBij relatie met een LSDeel object',
             spreadsheet_id='1iVs6wP1WcdHxEUsx5N_NlunvGU4LycRUO1_4j03Nwzo',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (s:onderdeel {isActief:TRUE}) 
WHERE (s:Stroomkring OR s:Laagspanningsbord) AND NOT EXISTS ((s)-[:HoortBij]->(:LSDeel {isActief:TRUE}))
RETURN s.uuid, s.naam"""

r.result_query = result_query
r.run_report()


