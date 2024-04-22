from DQReport import DQReport


class Report0119:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0119',
                               title='DNBHoogspanning en DNBLaagspanning hebben een installatieverantwoordelijke',
                               spreadsheet_id='1hGwws9A8U8F5dQZChGNDH4YOtiuB8LVq7Ovh93DmD2c',
                               datasource='Neo4J',
                               persistent_column='F')

        self.report.result_query = """
                MATCH (a:DNBHoogspanning|DNBLaagspanning {isActief:TRUE})-[r:HeeftBetrokkene]->(b:Agent)
                WHERE r.rol <> 'installatieverantwoordelijke'
                RETURN a.uuid, a.naam, a.typeURI, r.rol as relatie_rol, b.naam as agent_naam
                
                """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
