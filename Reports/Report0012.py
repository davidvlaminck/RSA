from DQReport import DQReport


class Report0012:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0012',
                               title='Camera\'s hebben een Bevestiging relatie tenzij ze tot een tunnel behoren',
                               spreadsheet_id='1ZHc-mdiViQlOKTUtcR_vzvk-DyFiqhwUv5Gf52Q6bm4',
                               datasource='Neo4J',
                               persistent_column='G')

        # TODO recheck query
        self.report.result_query = """OPTIONAL MATCH (c:Camera {isActief:TRUE})-[:HoortBij]->(i:installatie {isActief:TRUE})
        WHERE c IS NOT NULL AND NOT EXISTS((c)-[:Bevestiging]-()) AND NOT i.naampad CONTAINS "TUNNEL" AND NOT i.naampad CONTAINS "Tunnel"
        RETURN c.uuid AS camera_uuid, c.naam AS camera_naam, i.uuid AS installatie_uuid, i.naam AS installatie_naam, i.naampad AS installatie_naampad, i.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
