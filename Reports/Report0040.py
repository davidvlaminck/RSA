from DQReport import DQReport


class Report0040:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0040',
                               title='DNBLaagspanning/DNBHoogspanning hebben een HoortBij relatie naar LS/HS respectievelijk',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (dnbl:DNBLaagspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbl)-[:HoortBij]->(:LS {isActief: TRUE}))
            RETURN dnbl.uuid as uuid, dnbl.naam as naam, dnbl.typeURI as typeURI
            UNION
            MATCH (dnbh:DNBHoogspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbh)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN dnbh.uuid as uuid, dnbh.naam as naam, dnbh.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
