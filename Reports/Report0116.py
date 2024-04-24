from DQReport import DQReport


class Report0116:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0116',
                               title='De naam van de assets (DNBHoogSpanning of DNBLaagSpanning) is gelijk aan het eerste deel van het naampad van de installatie',
                               spreadsheet_id='11tU64Fc9Xh1IIlmufZ5yJ9Q99Sw4oP1kzCO0LrMbOn0',
                               datasource='Neo4J',
                               persistent_column='F',
                               link_type='eminfra'
                               )

        self.report.result_query = """
        //De naam van de assets (DNBHoogSpanning of DNBLaagSpanning) is gelijk aan het eerste deel van het naampad van de installatie
        MATCH (a:DNBHoogspanning|DNBLaagspanning {isActief:true}) -[r:HoortBij {isActief:TRUE}]->(b:installatie {isActief:true})
        WHERE NOT a.naam = head(split(b.naampad, '/'))
        RETURN
            b.uuid as uuid
            , b.typeURI as typeURI
            , b.naampad as legacy_naampad
            , a.uuid as otl_uuid
            , a.naam as otl_naam
        ORDER BY typeURI, uuid
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
