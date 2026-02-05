from lib.reports.DQReport import DQReport


class Report0008:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0008',
                               title='Camera\'s hebben HoortBij relatie met dezelfde naam',
                               spreadsheet_id='1I885ty8NfSdk0wKe4G6eJJ2fuY3wvgjUDw-ivUAVNVc',
                               datasource='Neo4J',
                               persistent_column='G')

        # TODO recheck query
        self.report.result_query = """OPTIONAL MATCH (c:onderdeel :Camera {isActief:TRUE})-[r:HoortBij]->(i:installatie {isActief:TRUE})
        WHERE NOT (i:PTZ OR i:AID OR i:CCTV) OR r IS NULL OR i.naam <> c.naam
        WITH c, i
        OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN c.uuid AS uuid_camera, c.naam AS camera_naam, a.naam as toezichter, i.uuid AS hoortbij_legacy_uuid, i.naam AS hoortbij_legacy_naam, i.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
