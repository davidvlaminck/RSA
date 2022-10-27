from DQReport import DQReport


class Report0041:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0041',
                               title='EnergiemeterDNB en ForfaitaireAansluiting hebben een HoortBij relatie naar een LS of HS',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (x {isActief: TRUE})
            WHERE (x:EnergiemeterDNB OR x:ForfaitaireAansluiting) AND NOT EXISTS((x)-[:HoortBij]->(:LS {isActief: TRUE})) AND NOT EXISTS((x)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
