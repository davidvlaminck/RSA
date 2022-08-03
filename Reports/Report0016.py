from DQReport import DQReport


class Report0016:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0016',
                               title='Netwerkpoorten hebben een Bevestiging relatie met een Netwerkelement of een Netwerkkaart',
                               spreadsheet_id='16NJCwhrHnYuz6Z9leqGswfOR0bt7EdBK_GonPB-3y7o',
                               datasource='Neo4J',
                               persistent_column='C')
        self.report.result_query = """
        MATCH (n:Netwerkpoort {isActief:TRUE})
        WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkkaart {isActief:TRUE})) and NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkelement {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
