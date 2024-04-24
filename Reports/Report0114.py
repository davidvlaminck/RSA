from DQReport import DQReport


class Report0114:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0114',
                               title='EAN Nummer niet als commentaar gedocumenteerd',
                               spreadsheet_id='188xxFUa1uZ8GPgwB9a2c0gtkrdtacg5ft5TkODanatk',
                               datasource='Neo4J',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
        // EAN wordt gecontroleerd door een regex match met 18 digits, starting with 54
        MATCH (a {isActief:true})
        where
            a.notitie =~ '^.*54\d{16}.*$'
        RETURN a.uuid, a.notitie, a.naampad, a.typeURI, a.isActief
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
