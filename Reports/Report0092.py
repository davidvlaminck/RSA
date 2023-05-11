from DQReport import DQReport


class Report0092:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0092',
                               title='VRI Wegkantkasten hebben een ingevulde verlichting',
                               spreadsheet_id='1NMv8jIX0x-WBOrks5fIyAL6FNjlwbKqOVJpFQBCfjrk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.heeftVerlichting IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
