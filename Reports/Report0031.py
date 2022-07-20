from DQReport import DQReport


r = DQReport(name='report0031',
             title="Netwerkementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
             spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (n:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) 
WHERE NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))
RETURN n.uuid, n.naam"""

r.result_query = result_query
r.run_report()
