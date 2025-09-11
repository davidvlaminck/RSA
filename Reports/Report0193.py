from DQReport import DQReport


class Report0193:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0193',
                               title='SegmentControllers hebben een (afgeleide) locatie',
                               spreadsheet_id='1O3e83o3Aa-b0eW3xMBjCZoG6b5vNfY9PAXmeULjo1as',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
        select
            a."uuid"
            , a.actief 
            , a.toestand 
            , a.naam 
            , at."label" 
            , l.geometrie
            , i.gebruikersnaam 
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        left join locatie l on a."uuid" = l.assetuuid 
        left join identiteiten i on a.toezichter = i."uuid" 
        where
            a.actief is true
            and a.assettype = 'f625b904-befc-4685-9dd8-15a20b23a58b' -- SegmentController (Legacy)
            and l.geometry is null
        order by a.toestand, a.naam
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
