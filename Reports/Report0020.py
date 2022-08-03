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

        self.report.result_query = """MATCH (gl:Zpad {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
        WITH gl, COUNT(p) AS aantal_poorten
        WHERE aantal_poorten = 2
        WITH collect(gl.uuid) AS good_paden
        MATCH (p:Zpad {isActief:TRUE} )
        WHERE NOT p.uuid IN good_paden
        RETURN p.uuid, p.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
