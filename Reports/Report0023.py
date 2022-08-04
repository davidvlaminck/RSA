from DQReport import DQReport


class Report0023:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0023',
                               title='Camera\'s hebben een toezichter',
                               spreadsheet_id='1jkBCSgtZ8jlwA-Ah62I17pVtybrqPZSreXgrC6kWKoQ',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (c:Camera {isActief:TRUE})
        WHERE NOT EXISTS ((c)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))
        RETURN c.uuid, c.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
