from DQReport import DQReport


class Report0046:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0046',
                               title='Een Onderbouw heeft steeds een ligtOp relatie naar een Geotextiel',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """
            MATCH (o:Onderbouw {isActief: TRUE})
            WHERE NOT EXISTS((o)-[:LigtOp]->(:Geotextiel {isActief: TRUE}))
            RETURN o.uuid as uuid, o.toestand as toestand
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
