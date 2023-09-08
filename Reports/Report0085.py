from DQReport import DQReport


class Report0085:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0085',
                               title='Verkeersregelaars hebben een ingevulde theoretische levensduur',
                               spreadsheet_id='11QZWCKGmGAkWWECLqtbuV4URFo3Gj4obrW4fMcEOT5s',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.theoretischeLevensduur IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
