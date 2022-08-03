from DQReport import DQReport


class Report0026:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0026',
                               title='Paden hebben een HoortBij relatie naar Zpad objecten',
                               spreadsheet_id='18KfmYhpxc75ECyN54WFtKrG4Hdz6GPCXzH5i8Zi0144',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Asset:Pad {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Asset:Zpad {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
