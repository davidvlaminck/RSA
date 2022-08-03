from DQReport import DQReport


class Report0002:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0002',
                               title='TLCfipoorten hebben een sturingsrelatie naar een Verkeersregelaar',
                               spreadsheet_id='1C4OvyX6uQfe3eKa8A_ClsTfnmAcBy-45Q-18htdxHHM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Asset :TLCfiPoort {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:Sturing]-(:Verkeersregelaar {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
