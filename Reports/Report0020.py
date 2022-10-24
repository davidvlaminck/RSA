from DQReport import DQReport


class Report0020:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0020',
                               title='Zpaden zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1dudUqdNZTf1lPcAFbv_kSTI0gIBvAkX0TUumvwR-O7M',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (z:Zpad {isActief:TRUE})
        WHERE z.toestand = "in-gebruik"
        OPTIONAL MATCH (z)<-[:HoortBij]-(n:Netwerkpoort {isActief:TRUE})
        WITH z, count(n) AS n_netwerkpoort
        WHERE n_netwerkpoort <> 2
        RETURN z.uuid, z.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
