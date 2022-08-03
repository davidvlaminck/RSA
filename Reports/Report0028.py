from DQReport import DQReport


class Report0028:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0028',
                               title='IP Netwerkelementen (niet merk Nokia of Ciena) hebben een HoortBij relatie met een legacy object van type IP',
                               spreadsheet_id='1wn05XDV1PkyVdGgDEO3yUU0Jqf3t6asGH0SyGXQQWS8',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """MATCH (n:Netwerkelement {isActief:TRUE})
        WHERE NOT n.merk IN ['NOKIA', 'Ciena'] AND NOT EXISTS ((n)-[:HoortBij]->(:IP {isActief:TRUE}))
        RETURN n.uuid, n.naam, n.merk"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
