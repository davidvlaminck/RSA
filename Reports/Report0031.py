from DQReport import DQReport


class Report0031:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0031',
                               title="Netwerkelementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
                               spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) 
        WHERE NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
