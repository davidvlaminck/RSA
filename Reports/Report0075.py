from DQReport import DQReport


class Report0075:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0075',
                               title='Verkeersregelaars hebben een toezichter',
                               spreadsheet_id='1n2_75LTrJ9UazN6qQaDSZ6LT2q8IDjxJLaRmqUnikbs',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WHERE NOT EXISTS ((a)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
