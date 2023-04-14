from DQReport import DQReport


class Report0034:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0034',
                               title="NNI Netwerkpoorten hebben een Sturing relatie met een NNI Netwerkpoort",
                               spreadsheet_id='1Q0ypijGhIMmax4iR3DHHu4FMYVbkU_LCQhBAyzbIA2k',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})-[:Bevestiging]-(:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) 
        WHERE NOT EXISTS ((n)-[:Sturing]-(:Netwerkpoort {isActief:TRUE, type:'NNI'}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
