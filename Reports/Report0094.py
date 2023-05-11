from DQReport import DQReport


class Report0094:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0094',
                               title='VRI Wegkantkasten hebben een kastmateriaal',
                               spreadsheet_id='1bxcPvW1g-11exvZmVbsvZZRvfk0GEhN2HGxd4AUHdwQ',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.kastmateriaal IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
