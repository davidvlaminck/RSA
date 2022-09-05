from DQReport import DQReport


class Report0037:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0037',
                               title="L2 switches horen bij een asset die gevoed wordt",
                               spreadsheet_id='1mPx2y3XvOGNCRoYPLTHv6Xb5kn4bQCt3Aii0zT7ZdUc',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'})
        WHERE NOT EXISTS ((n)-[:HoortBij]-()<-[:Voedt]-())
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

