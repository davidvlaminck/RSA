from DQReport import DQReport


r = DQReport(name='report0012',
             title='Camera\'s hebben een Bevestiging relatie tenzij ze tot een tunnel behoren',
             spreadsheet_id='1ZHc-mdiViQlOKTUtcR_vzvk-DyFiqhwUv5Gf52Q6bm4',
             datasource='Neo4J',
             persistent_column='G')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (c:Camera {isActief:TRUE})-[:HoortBij]->(i:installatie)
WHERE c IS NOT NULL AND NOT EXISTS((c)-[:Bevestiging]-()) AND NOT i.naampad CONTAINS "TUNNEL" AND NOT i.naampad CONTAINS "Tunnel"
RETURN c.uuid AS camera_uuid, c.naam AS camera_naam, i.uuid AS installatie_uuid, i.naam AS installatie_naam, i.naampad AS installatie_naampad, i.typeURI"""

r.result_query = result_query
r.run_report()


