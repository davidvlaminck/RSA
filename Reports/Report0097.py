from DQReport import DQReport


class Report0097:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0097',
                               title='VRI Wegkantkasten hebben een toestand',
                               spreadsheet_id='1xmV-7Xn9fAozRtRBU_MueRcjEOMlfBTcIDoDkG-Y-Es',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.toestand IS NULL OR k.toestand = 'in-ontwerp')
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
