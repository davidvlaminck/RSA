from DQReport import DQReport


class Report0095:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0095',
                               title='VRI Wegkantkasten hebben een ingevulde verfraaid',
                               spreadsheet_id='1Z_q0uTdTuxKhUpT_BPZDcW-uiHXFc7WpStnu36IiSbc',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.verfraaid IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
