from DQReport import DQReport


class Report0090:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0090',
                               title='VRI Wegkantkasten hebben een indelingsplan',
                               spreadsheet_id='12-I-t8_kBb2TPfiFzDbdAOa0QwlscXvHBWjIos6ucbI',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.`indelingsplan.bestandsnaam` IS NULL OR k.`indelingsplan.uri` IS NULL)
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
