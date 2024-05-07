from DQReport import DQReport


class Report0126:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0126',
                               title='KabelnetBuis HeeftNetwerktoegang tot een BeschermBuis',
                               spreadsheet_id='1_U31z99SVb2B_BbiXd9ZEB-tmwI4KYM17amUYWinkN0',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetBuis HeeftNetwerktoegang tot een BeschermBuis
        MATCH (n:KabelnetBuis {isActief:true})-[r {isActief:TRUE}]-(m:Beschermbuis {isActief:TRUE})
        WHERE r.type <> 'HeeftNetwerktoegang'
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
