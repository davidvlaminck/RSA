from DQReport import DQReport


r = DQReport(name='report0005',
             title='Wegkantkasten hebben een HoortBij relatie naar Kast objecten',
             spreadsheet_id='1_yLv--qorkqbx5ym_qBUTxc6b7mOvdm5kD8SrWPkB5I',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (a:Asset :Wegkantkast {isActief:TRUE}) 
WHERE NOT EXISTS ((a)-[:HoortBij]->(:Kast {isActief:TRUE}))
RETURN a.uuid, a.naam"""

r.result_query = result_query
r.run_report()
    

