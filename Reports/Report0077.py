from DQReport import DQReport


class Report0077:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0077',
                               title='Verkeersregelaars hebben een ingevulde datum oprichting object',
                               spreadsheet_id='10K9cwkJIJQ2sXb71rvqm1MqtSj5k2M5FKtYUhE4mf2E',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.datumOprichtingObject IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
