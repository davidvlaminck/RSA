from lib.reports.DQReport import DQReport


class Report0027:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0027',
                               title='Objecten zonder relaties en geometrie',
                               spreadsheet_id='1LVs9xrCLKOya5FU3GdF1DPRTEzEtDkRskOp5vkIg130',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """MATCH (o:onderdeel {isActief:TRUE})
        WHERE NOT EXISTS ((o)--(:Asset {isActief:TRUE})) AND (o.geometry = '' OR o.geometry IS NULL)
        WITH o
        OPTIONAL MATCH (o:onderdeel {isActief:TRUE})-[r:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN o.uuid, o.naam, o.typeURI, a.naam as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
