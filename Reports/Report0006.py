from DQReport import DQReport


class Report0006:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0006',
                               title='Wegkantkasten hebben een HoortBij relatie naar Kast objecten',
                               spreadsheet_id='1_yLv--qorkqbx5ym_qBUTxc6b7mOvdm5kD8SrWPkB5I',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Asset :Wegkantkast {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Kast {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
