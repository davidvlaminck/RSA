from DQReport import DQReport
from OTLCursorPool import OTLCursorPool


class Report0043:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0043',
                               title='Er zijn geen instanties van classes die deprecated zijn in de OTL',
                               spreadsheet_id='',
                               datasource='PostGIS',
                               persistent_column='D')

        otl_cursor = OTLCursorPool.get_cursor()
        deprecated_classes = otl_cursor.execute("""
            SELECT oc.uri
            FROM OSLOClass oc
            WHERE oc.deprecated_version IS NOT NULL AND oc.deprecated_version != ""
        """).fetchall()

        self.report.result_query = """
            SELECT a.uuid AS asset_uuid, a_t.uri AS assettype_uri, a.toestand AS asset_toestand 
            FROM assets a
            INNER JOIN assettypes AS a_t ON (a.assettype = a_t.uuid)
            INNER JOIN (VALUES {}) AS d_c(uri) ON (a_t.uri = d_c.uri)
            WHERE a.actief = TRUE
        """.format(",".join(["({})".format(d) for d in deprecated_classes]))

    def run_report(self, sender):
        self.report.run_report(sender=sender)
