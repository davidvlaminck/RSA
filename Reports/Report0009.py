from DQReport import DQReport


r = DQReport(name='report0009',
             title='Omvormers hebben een Bevestiging relatie met een Behuizing',
             spreadsheet_id='1A4kata3Eg9fMjsUE8Za5XEtcF7JEm_-IftHhGz6SnJo',
             datasource='Neo4J',
             persistent_column='F')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (a:onderdeel :Omvormer {isActief:TRUE})-[r:Bevestiging]->(o:onderdeel {isActief:TRUE})
WHERE NOT (o:Wegkantkast OR o:Montagekast) OR r IS NULL
RETURN a.uuid AS uuid_camera, a.naam AS camera_naam, o.uuid AS geen_behuizing_uuid, o.naam AS geen_behuizing_naam, o.typeURI"""

r.result_query = result_query
r.run_report()


