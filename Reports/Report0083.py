from DQReport import DQReport


class Report0083:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0083',
                               title='Verkeersregelaars hebben een voltage lampen die 42 of 230 is',
                               spreadsheet_id='1KQU0DrpB-LmU-DNOSzshYSA14aRmeomYcMF1xTm2Zek',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.voltageLampen IS NULL OR NOT a.voltageLampen IN ['42', '230']
RETURN a.uuid, a.naam, a.voltageLampen"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
