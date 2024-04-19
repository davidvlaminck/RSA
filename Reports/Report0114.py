from DQReport import DQReport


class Report0114:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0114', title='EAN Nummer niet als commentaar gedocumenteerd',
                               spreadsheet_id='188xxFUa1uZ8GPgwB9a2c0gtkrdtacg5ft5TkODanatk', datasource='Neo4J',
                               persistent_column='I')

        self.report.result_query = """
        // EAN wordt gecontroleerd door een regex match met 18 digits, starting with 54
        MATCH (a {isActief:true})-[r:HoortBij {isActief:true}]->(b)
        where
            a.notitie =~ '54\d{16}'
            OR
            b.notitie =~ '54\d{16}'
        RETURN a.assetIdUri, a.uuid, a.notitie, a.eanNummer, b.assetIdUri, b.uuid, b.eanNummer, b.notitie
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
