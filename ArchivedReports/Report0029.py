from lib.reports.DQReport import DQReport


class Report0029:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0029',
                               title='IP elementen hebben een bijbehorend Netwerkelement',
                               spreadsheet_id='1VJmqHesEfOaZzYD8rZdZUNeKUoCBKMetgltL74bX9jk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (i:IP {isActief:TRUE, `tz:toezichtgroep.tz:referentie`:'EMT_TELE'})
        WHERE NOT EXISTS((i)<-[:HoortBij]-(:Netwerkelement {isActief:TRUE}))
        RETURN i.uuid, i.naam, i.naampad, i.`tz:toezichter.tz:gebruikersnaam` as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
