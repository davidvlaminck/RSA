from DQReport import DQReport


class Report0114:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0114',
                               title='EAN Nummer niet als commentaar gedocumenteerd',
                               spreadsheet_id='188xxFUa1uZ8GPgwB9a2c0gtkrdtacg5ft5TkODanatk',
                               datasource='PostGIS',
                               persistent_column='J',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a."uuid",
                a.naampad,
                at.uri,
                a.actief, 
                a.toestand,
                a.commentaar,
                i.voornaam,
                i.naam, 
                i.gebruikersnaam 
            from assets a
            left join assettypes at on a.assettype = at."uuid"
            left join identiteiten i on a.toezichter = i."uuid"
            where
                a.actief is true
                and
                a.assettype not in ('92240246-a6b7-49ee-9726-a6d145e79c86')
                and
                a.commentaar ~ '54[0-9]{16}'
            order by at.uri, a.uuid
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
