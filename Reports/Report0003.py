from DQReport import DQReport


class Report0003:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0003',
                               title='Verkeersregelaars hebben een Bevestiging relatie naar een Wegkantkast',
                               spreadsheet_id='1tud5st23sWAKYxdtGUmNHS1Tt54GW31HwkJPaXYXrtE',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:Bevestiging]-(:Wegkantkast {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
