from DQReport import DQReport


class Report0042:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0042',
                               title='EnergiemeterDNB en ForfaitaireAansluiting worden gevoed door een DNBLaagspanning',
                               spreadsheet_id='1QloH-HeEqyMpg2hnbAPSv8tLpxsLDOaXcPMywTj_Oi4',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (x {isActief: TRUE})
            WHERE (x:EnergiemeterDNB OR x:ForfaitaireAansluiting) AND NOT EXISTS((x)<-[:Voedt]-(:DNBLaagspanning {isActief: TRUE}))
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
