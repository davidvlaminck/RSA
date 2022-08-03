from DQReport import DQReport


class Report0017:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0017',
                               title='Netwerkkaarten hebben een Bevestiging relatie met een Netwerkelement',
                               spreadsheet_id='1UfYhxcM0z8uq9-GwfDJhHNVpuhoWtUprrPGMfPSXeGk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkkaart {isActief:TRUE})
        WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkelement {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
