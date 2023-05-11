from DQReport import DQReport


class Report0089:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0089',
                               title='VRI Wegkantkasten hebben een elektrisch schema',
                               spreadsheet_id='1kt7UYbiXzf222WnZB-dTTYzp3cIMjAA9WFi0Z2BvvCU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.`elektrischSchema.bestandsnaam` IS NULL OR k.`elektrischSchema.uri` IS NULL)
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
