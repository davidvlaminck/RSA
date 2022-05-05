from DQReport import DQReport


r = DQReport(name='report0008',
             title='Camera\'s hebben HoortBij relatie met dezelfde naam',
             spreadsheet_id='1I885ty8NfSdk0wKe4G6eJJ2fuY3wvgjUDw-ivUAVNVc',
             datasource='Neo4J',
             persistent_column='F')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (a:onderdeel :Camera {isActief:TRUE})-[r:HoortBij]->(i:installatie {isActief:TRUE})
WHERE NOT (i:PTZ OR i:AID OR i:CCTV) OR r IS NULL OR i.naam <> a.naam
RETURN a.uuid AS uuid_camera, a.naam AS camera_naam, i.uuid AS hoortbij_legacy_uuid, i.naam AS hoortbij_legacy_naam, i.typeURI"""

r.result_query = result_query
r.run_report()


