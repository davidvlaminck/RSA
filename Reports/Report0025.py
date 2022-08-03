from DQReport import DQReport


class Report0025:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0025',
                               title='Linken hebben een HoortBij relatie naar Pad objecten',
                               spreadsheet_id='1PwWn1E4VRsXRa8L7Lh0Pmjy1Z0ZKCoclDO0bvHx3EaY',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Asset :Link {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Pad {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
