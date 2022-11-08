from DQReport import DQReport
from OTLCursorPool import OTLCursorPool

class Report0043:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0043',
                               title='Er zijn geen instanties van classes die deprecated zijn in de OTL',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='D')

        otl_cursor = OTLCursorPool().get_cursor()
        deprecated_classes = [row[0] for row in otl_cursor.execute("""
            SELECT c.uri 
            FROM OSLOClass as c
            WHERE c.deprecated_version IS NOT NULL AND c.deprecated_version != ""
        """).fetchall()]

        self.report.result_query = """
            UNWIND {} AS c_uri
            WITH c_uri, split(c_uri, '#')[-1] as c_name
            MATCH (x {{isActief: TRUE}})
            WHERE c_name in LABELS(x) AND x.typeURI = c_uri
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI
        """.format(deprecated_classes)

    def run_report(self, sender):
        self.report.run_report(sender=sender)
