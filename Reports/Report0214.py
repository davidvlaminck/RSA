from DQReport import DQReport


class Report0214:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0214',
                               title='Actieve assets (Legacy) wiens assettype inactief is',
                               spreadsheet_id='1gmrHAnR-t459u8jY9hfoidWo3hRWg7zRY6aRDSgW2lM',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a."uuid", 
                a.actief as "asset_status", 
                a.naam, 
                a.naampad, 
                at.uri,
                at."label", 
                at.actief as "assettype_status"
            from assets a
            left join assettypes at on a.assettype = at."uuid"
            where
                a.actief is true
                and 
                at.actief is false
                and
                at.uri ~ 'https://lgc.*'
            order by at.uri asc;
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
