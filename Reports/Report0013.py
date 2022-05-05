from DQReport import DQReport


r = DQReport(name='report0013',
             title='Stroomkringen hebben een Bevestiging relatie met een Laagspanningsbord',
             spreadsheet_id='1az4rh44wIf0KkILgQqV0iJeb47SbRW-dgq_DP3GDDeo',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (s:Stroomkring {isActief:TRUE}) 
WHERE NOT EXISTS ((s)-[:Bevestiging]-(:Laagspanningsbord {isActief:TRUE}))
RETURN s.uuid, s.naam"""

r.result_query = result_query
r.run_report()


