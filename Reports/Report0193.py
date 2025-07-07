from DQReport import DQReport


class Report0193:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0193',
                               title='SegmentControllers hebben een (afgeleide) locatie',
                               spreadsheet_id='1O3e83o3Aa-b0eW3xMBjCZoG6b5vNfY9PAXmeULjo1as',
                               datasource='PostGIS',
                               persistent_column='G')

        self.report.result_query = """
        select
            a."uuid"
            , a.actief 
            , a.toestand 
            , a.naam 
            , at."label" 
            , g.wkt_string 
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        left join geometrie g on a."uuid" = g.assetuuid
        where
            a.actief is true
            and a.assettype = 'f625b904-befc-4685-9dd8-15a20b23a58b' -- SegmentController (Legacy)
            and g.geometry is null
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
