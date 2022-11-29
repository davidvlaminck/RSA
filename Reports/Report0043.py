from DQReport import DQReport
from OTLCursorPool import OTLCursorPool


class Report0043:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0043',
                               title='Instanties van deprecated classes',
                               spreadsheet_id='1rpYt_EKa5YOCDBdzmrAcV6vwoy3hccblR6_spaV2ziI',
                               datasource='PostGIS',
                               persistent_column='D')

        otl_cursor = OTLCursorPool.get_cursor()
        deprecated_classes = otl_cursor.execute("""
            SELECT o_c.uri
            FROM OSLOClass o_c
            WHERE o_c.deprecated_version IS NOT NULL AND o_c.deprecated_version != ""
        """).fetchall()

        self.report.result_query = """
            SELECT a.uuid AS asset_uuid, a_t.uri AS assettype_uri, a.toestand AS asset_toestand 
            FROM assets a
            INNER JOIN assettypes AS a_t ON (a.assettype = a_t.uuid)
            INNER JOIN (VALUES {}) AS d_c(uri) ON (a_t.uri = d_c.uri)
            WHERE a.actief = TRUE
        """.format(",".join(["('{}')".format(d[0]) for d in deprecated_classes]))

    def run_report(self, sender):
        self.report.run_report(sender=sender)
