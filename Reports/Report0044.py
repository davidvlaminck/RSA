from DQReport import DQReport
from OTLCursorPool import OTLCursorPool


class Report0044:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0044',
                               title='Ingevulde deprecated attributen',
                               spreadsheet_id='1GFfEoWVvi0-BpFvrPQUG6w5AuMcoyVk9Kutf9ux8bOE',
                               datasource='PostGIS',
                               persistent_column='E')

        otl_cursor = OTLCursorPool.get_cursor()
        deprecated_attributes = otl_cursor.execute("""
            SELECT o_a.uri
            FROM OSLOAttributen o_a
            WHERE o_a.deprecated_version IS NOT NULL AND o_a.deprecated_version != ""
        """).fetchall()

        self.report.result_query = """
            SELECT a.uuid AS asset_uuid, a.toestand AS asset_toestand, ab.uri AS attribuut_uri, a_w.waarde AS attribuut_waarde
            FROM assets a
            INNER JOIN attribuutwaarden AS a_w ON (a.uuid = a_w.assetuuid)
            INNER JOIN attributen AS ab ON (a_w.attribuutuuid = ab.uuid)
            INNER JOIN (values {}) AS d_a(uri) ON (ab.uri = d_a.uri)
            WHERE a.actief = TRUE AND a_w NOTNULL
        """.format(",".join(["('{}')".format(d[0]) for d in deprecated_attributes]))

    def run_report(self, sender):
        self.report.run_report(sender=sender)
