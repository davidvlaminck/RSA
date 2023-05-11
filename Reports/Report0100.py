from DQReport import DQReport


class Report0100:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0100',
                               title='Verkeersregelaars hebben een sturingsrelatie naar een TLCfiPoort',
                               spreadsheet_id='1C4OvyX6uQfe3eKa8A_ClsTfnmAcBy-45Q-18htdxHHM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:Sturing]-(:TLCfiPoort {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
