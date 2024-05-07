from DQReport import DQReport


class Report0127:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0127',
                               title='KabelnetBuis heeft een relatie met een andere asset',
                               spreadsheet_id='1miMzTSeLtpLlK61lijv1Fzh88xC4U9RKVmwZnMjmdPU',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetBuis zonder relatie
        MATCH (n:KabelnetBuis)
        WHERE NOT (n)--()
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
