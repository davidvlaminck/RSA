from DQReport import DQReport


class Report0098:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0098',
                               title='VRI Wegkantkasten hebben een theoretische levensduur',
                               spreadsheet_id='1guhz-Sb-eBSFWEpf2Ayn1VboyTJG98lINM3_ppEROfA',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.theoretischeLevensduur IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
