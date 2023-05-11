from DQReport import DQReport


class Report0091:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0091',
                               title='VRI Wegkantkasten hebben een ingevulde maaibescherming',
                               spreadsheet_id='1GpRwKm-Ua-HedNI7PGULSfLbZ8PekT8vZk4NvVdBCeI',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.heeftMaaibescherming IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
