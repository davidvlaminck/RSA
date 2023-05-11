from DQReport import DQReport


class Report0096:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0096',
                               title='VRI Wegkantkasten hebben een type',
                               spreadsheet_id='1QprGpAuoCALC981B02kgAQJhj3CV1B6KYXPTF1pgacU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.type IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
