from DQReport import DQReport


class Report0004:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0004',
                               title='Verkeersregelaars hebben een unieke naam',
                               spreadsheet_id='1aGZFPAeFgkQgU2XcrKhVKK1NPu-OEPuskPvWsnAyEYU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WITH a.naam AS naam, COUNT(a.naam) AS aantal
        WHERE aantal > 1
        MATCH (b:Verkeersregelaar {isActief:TRUE, naam:naam})
        RETURN b.uuid, b.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
