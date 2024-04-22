from DQReport import DQReport


class Report0121:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0121',
                               title='Netwerkpoorten moeten een naam hebben en deze moet uniek zijn',
                               spreadsheet_id='1QPnohwuI7ziIFU2wac_9ZbOcJWr20asu4gvsr0t3x3E',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """
            MATCH (n:Netwerkpoort)
            WITH n.naam AS naam, count(n.naam) AS aantal, collect(n) AS nodes
            WHERE naam is not null and aantal > 1
            UNWIND nodes AS node
            RETURN node.uuid, node.naam, aantal, node.type, node.merk, node.assetIdUri
            ORDER BY aantal DESC
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
