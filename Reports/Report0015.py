from DQReport import DQReport


class Report0015:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0015',
                               title='Camera\'s hebben een unieke naam',
                               spreadsheet_id='1GM6mBwfsLkEELjroSw-df6A2HXSQnOFAeudUzTybMQE',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Camera {isActief:TRUE})
        WITH a.naam AS naam, COUNT(a.naam) AS aantal
        WHERE aantal > 1
        MATCH (b:Camera {isActief:TRUE, naam:naam})
        RETURN b.uuid, b.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
