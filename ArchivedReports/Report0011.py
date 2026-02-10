from lib.reports.DQReport import DQReport


class Report0011:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0011',
                               title='Omvormers en PoEInjectors hebben een HoortBij relatie naar OmvormerLegacy of Encoder objecten',
                               spreadsheet_id='1MQ4Xw31rYzjTzbfIc3a4VFsNq8a1M3lu6_Ly2OE3Opk',
                               datasource='Neo4J',
                               persistent_column='D')

        # query that fetches uuids of results
        self.report.result_query = """MATCH (o {isActief:TRUE})
        WHERE (o:Omvormer OR o:PoEInjector) AND NOT EXISTS ((o)-[:HoortBij]->(:Encoder {isActief:TRUE})) AND NOT EXISTS ((o)-[:HoortBij]->(:OmvormerLegacy {isActief:TRUE}))
        WITH o
        OPTIONAL MATCH (o)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN o.uuid, o.naam, a.naam as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
