from DQReport import DQReport


class Report0079:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0079',
                               title='Verkeersregelaars hebben een merk',
                               spreadsheet_id='1xdMtHKwBHN23eNMjAKyAVvyl2oAQuzauefuOx6jEQNk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.merk IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
