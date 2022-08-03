from DQReport import DQReport


class Report0013:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0013',
                               title='Stroomkringen hebben een Bevestiging relatie met een Laagspanningsbord',
                               spreadsheet_id='1az4rh44wIf0KkILgQqV0iJeb47SbRW-dgq_DP3GDDeo',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (s:Stroomkring {isActief:TRUE}) 
        WHERE NOT EXISTS ((s)-[:Bevestiging]-(:Laagspanningsbord {isActief:TRUE}))
        RETURN s.uuid, s.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
