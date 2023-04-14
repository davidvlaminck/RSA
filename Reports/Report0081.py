from DQReport import DQReport


class Report0081:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0081',
                               title='Verkeersregelaars hebben als naam een conforme installatienummer',
                               spreadsheet_id='1v7sqt0OumZ0rEhRVFTwnl_4vNoWj3G0QSsUTKHxSOaE',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.naam is NULL OR NOT (a.naam =~ '^\d{3}A\d$' OR a.naam =~ '^\d{3}C\d$' OR a.naam =~ '^\d{3}G\d$' OR a.naam =~ '^W[WO]\d{4}$')
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
