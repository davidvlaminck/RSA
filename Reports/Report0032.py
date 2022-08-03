from DQReport import DQReport


class Report0032:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0032',
                               title="Netwerkpoorten hebben een type",
                               spreadsheet_id='1CNSGgZbARVwRzrMB5a2LrSz-HJblvzAGWODsPOFE1jo',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})-[:Bevestiging]-(e:Netwerkelement {isActief:TRUE})
        WHERE NOT e.merk IN ['NOKIA', 'Ciena']
        WITH n
        WHERE n.type IS NULL 
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
