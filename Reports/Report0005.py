from DQReport import DQReport


class Report0005:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0005',
                               title='Verkeersregelaars en TLCfiPoorten hebben een HoortBij relatie naar VRLegacy objecten',
                               spreadsheet_id='1daDivHkKfMRamwgpty9swGF4Kz68MBjJlSE5SR2GqFQ',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (a:onderdeel {isActief:TRUE}) 
        WHERE (a:Verkeersregelaar OR a:TLCfiPoort) AND NOT EXISTS ((a)-[:HoortBij]->(:VRLegacy {isActief:TRUE}))
        RETURN a.uuid, a.naam, a.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
