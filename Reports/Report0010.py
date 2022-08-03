from DQReport import DQReport


class Report0010:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0010',
                               title='Camera\'s zijn het doel van een Voedt relatie met een Stroomkring of PoEInjector',
                               spreadsheet_id='1MzUeaGLeqV78IMBuTTFoM47y4nXja993AZnZF21Zu2U',
                               datasource='Neo4J',
                               persistent_column='D')

        # query that fetches uuids of results
        self.report.result_query = """MATCH (c:Camera {isActief:TRUE})
        WHERE NOT EXISTS ((c)<-[:Voedt]-(:Stroomkring {isActief:TRUE})) AND NOT EXISTS ((c)<-[:Voedt]-(:PoEInjector {isActief:TRUE}))
        WITH c
        OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN c.uuid, c.naam, a.naam as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
