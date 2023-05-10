from DQReport import DQReport


class Report0086:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0087',
                               title='VRI Wegkantkasten hebben een ingevulde datum oprichting object',
                               spreadsheet_id='13Y1AmHPji5z-Zy-uDF6-YstSF0DKDx2oKUHCs7iU6mU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(Verkeersregelaar {isActief:TRUE}) 
WHERE k.datumOprichtingObject IS NOT NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
