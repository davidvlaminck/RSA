from DQReport import DQReport


class Report0030:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0030',
                               title='Netwerkelementen hebben een (afgeleide) locatie',
                               spreadsheet_id='1ZAZ8chzMbLEyGd-cbZM6S7Uw4aNOrBmAE1KWnbyvdK4',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """
        // Report 0030
        MATCH (n:Netwerkelement {isActief: TRUE})
        WHERE (n.geometry IS NULL OR n.geometry = '')
        WITH n
        OPTIONAL MATCH (n)-[:HoortBij]-(n2)
        WHERE n2.isActief = TRUE
        WITH n, collect(n2) AS relatedNodes
        WHERE ALL(node IN relatedNodes WHERE node.geometry IS NULL OR node.geometry = '')
        RETURN n.uuid as uuid, n.naam as naam
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
