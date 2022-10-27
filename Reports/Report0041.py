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

        self.report.result_query = """MATCH (e:EnergiemeterDNB {isActief: TRUE})
            WHERE NOT EXISTS((e)-[:HoortBij]->(:LS {isActief: TRUE})) AND NOT EXISTS((e)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN e.uuid as uuid, e.naam as naam, e.typeURI as typeURI
            UNION
            MATCH (f:ForfaitaireAansluiting {isActief: TRUE})
            WHERE NOT EXISTS((f)-[:HoortBij]->(:LS {isActief: TRUE})) AND NOT EXISTS((f)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN f.uuid as uuid, f.naam as naam, f.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
