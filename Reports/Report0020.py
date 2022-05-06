from DQReport import DQReport


r = DQReport(name='report0020',
             title='Zpaden zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
             spreadsheet_id='1dudUqdNZTf1lPcAFbv_kSTI0gIBvAkX0TUumvwR-O7M',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """MATCH (gl:Zpad {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
WITH gl, COUNT(p) AS aantal_poorten
WHERE aantal_poorten = 2
WITH collect(gl.uuid) AS good_paden
MATCH (p:Zpad {isActief:TRUE} )
WHERE NOT p.uuid IN good_paden
RETURN p.uuid, p.naam"""

r.result_query = result_query
r.run_report()


