from DQReport import DQReport


class Report0014:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0014',
                               title='Stroomkringen en Laagspanningsborden hebben een HoortBij relatie met een LSDeel object',
                               spreadsheet_id='1iVs6wP1WcdHxEUsx5N_NlunvGU4LycRUO1_4j03Nwzo',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (s:onderdeel {isActief:TRUE}) 
        WHERE (s:Stroomkring OR s:Laagspanningsbord) AND NOT EXISTS ((s)-[:HoortBij]->(:LSDeel {isActief:TRUE}))
        RETURN s.uuid, s.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
