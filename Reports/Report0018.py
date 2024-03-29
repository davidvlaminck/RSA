from DQReport import DQReport


class Report0018:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0018',
                               title='Linken zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1U_27rorzzxcoBOxLoHIN8Vt20idDafrb5DGE_ECWVAw',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (gl:Link {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
        WITH gl, COUNT(p) AS aantal_poorten
        WHERE aantal_poorten = 2
        WITH collect(gl.uuid) AS good_links
        MATCH (l:Link {isActief:TRUE} )
        WHERE NOT l.uuid IN good_links
        RETURN l.uuid, l.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
