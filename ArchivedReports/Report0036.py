from lib.reports.DQReport import DQReport


class Report0036:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0036',
                               title="Netwerkpoorten met type 'UNI' hebben een hoortbij relatie naar installatie VLAN",
                               spreadsheet_id='14ecrURzs2O61GsGpiFvd85MuwX-A69gbh6tP37X3idQ',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'UNI'})-[:Bevestiging]-(:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) 
        WHERE NOT EXISTS ((n)-[:HoortBij]->(:VLAN {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
