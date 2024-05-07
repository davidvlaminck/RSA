from DQReport import DQReport


class Report0124:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0124',
                               title='KabelnetToegang HeeftNetwerktoegang tot een Behuizing',
                               spreadsheet_id='1Fia3N3bXG7LXBSbcst7jDM5N8Lr9HXHc3eCVcgNIdrM',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetToegang heeft een relatie "heeftNetwerkToegang" naar een asset van het type behuizing (gebouw, lokaal, indoorkast, cabine, wegkantkast, technischePut, montagekast). De status van beide assets en de relatie tussen beide is actief.
        MATCH (n:KabelnetToegang {isActief:True})-[r {isActief:TRUE}]-(m:Gebouw|Lokaal|IndoorKast|Cabine|Kast|IndoorKast|Wegkantkast|Montagekast|Hulppostkast|TechnischePut {isActief:True})
        WHERE r.type <> "HeeftNetwerktoegang"
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
