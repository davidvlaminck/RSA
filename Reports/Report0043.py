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
        deprecated_classes = otl_cursor.execute("""
            SELECT c.name, c.deprecated_version
            FROM OSLOClass as c
            WHERE c.deprecated_version IS NOT NULL AND c.deprecated_version != '' 
        """).fetchall()

        self.report.result_query = """MATCH (x) 
            UNWIND labels(x) as label
            WITH x, label
            WHERE label IN {}
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI""".format(deprecated_classes)

    def run_report(self, sender):
        self.report.run_report(sender=sender)
