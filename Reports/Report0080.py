from DQReport import DQReport


class Report0080:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0080',
                               title='Verkeersregelaars hebben een modelnaam',
                               spreadsheet_id='1JVX_XvZVgys7ntqWMDn32RolZPg_BvXpBIclMmQXxKI',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.modelnaam IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
