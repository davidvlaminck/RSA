from DQReport import DQReport


class Report0099:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0099',
                               title='VRI Wegkantkasten hebben een conforme naam',
                               spreadsheet_id='1tTJMTTWFLY9VV0imGZPRSCrC4qEULV9tWviO8JBQIfA',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.naam is NULL OR NOT (k.naam =~ '^\d{3}[ACG]\dX01$' OR k.naam =~ '^W[WO]\d{4}X01$'))
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
