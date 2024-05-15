from DQReport import DQReport


class Report0125:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0125',
                               title='KabelnetToegang heeft een relatie met een andere asset',
                               spreadsheet_id='1FVilNqQXxNI0HB9Zu2Dc4e9McODPw-eDPeG0h3i0_x4',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetToegang zonder relatie
        MATCH (n:KabelnetToegang {isActief:True})
        WHERE NOT (n)--()
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
