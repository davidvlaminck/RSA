from DQReport import DQReport


class Report0083:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0086',
                               title='Verkeersregelaars hebben een ingevulde toestand',
                               spreadsheet_id='1EJjhp70-7bbrHaTbqPuZdn86rrXw30TEUYns7Kvi1dQ',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MMATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.toestand IS NULL OR a.toestand = 'in-ontwerp'
RETURN a.uuid, a.naam, a.toestand   """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
