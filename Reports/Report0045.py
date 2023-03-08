from DQReport import DQReport


class Report0045:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0045',
                               title='Een BitumineuzeLaag heeft steeds een ligtOp relatie naar een Onderbouw',
                               spreadsheet_id='1WRzZGpDXwtjg0CYa54pQBeYPfosNqe1-4g5c_xKWvrM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """
            MATCH (b:BitumineuzeLaag {isActief: TRUE})
            WHERE NOT EXISTS((b)-[:LigtOp]->(:Onderbouw {isActief: TRUE}))
            RETURN b.uuid AS uuid, b.toestand AS toestand
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
