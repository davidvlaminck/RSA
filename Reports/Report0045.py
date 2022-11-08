from DQReport import DQReport


class Report0045:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0045',
                               title='Een BitumineuzeLaag heeft steeds een ligtOp relatie naar een Onderbouw',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """
        MATCH (b:BitumineuzeLaag)
        WHERE NOT EXISTS((b)-[:LigtOp]->(:Onderbouw))
        RETURN b.uuid as uuid, b.name as name"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
