from DQReport import DQReport


class Report0033:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0033',
                               title="VLAN objecten hebben een HoortBij relatie met een L2AccesStructuur",
                               spreadsheet_id='12urCVlUXm_KbNCrQS1MH5kVqNKak3n5DdQlAnk8mn9w',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:VLAN {isActief:TRUE}) 
        WHERE NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
