from DQReport import DQReport


class Report0093:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0093',
                               title='VRI Wegkantkasten hebben een ingress protection klasse',
                               spreadsheet_id='1avx8BOU2bvwYBmE0_ntKVcz6Uy3-o72mNXgHZMWeaSU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.ipKlasse IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
