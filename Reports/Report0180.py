from DQReport import DQReport


class Report0180:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0180', title='SegmentControllers hun serienummer volgt een bepaalde regex validatie',
                               spreadsheet_id='1CQgzLh1L0qEdVpjRz2NiKnZPkIuphc8BvOk1J8a1q_0', datasource='PostGIS',
                               persistent_column='F', link_type='eminfra')

        self.report.result_query = """
        WITH cte_segmentcontroller AS (
            SELECT 
                a.uuid,
                a.naam,
                a.naampad,
                aw.waarde AS serienummer,
                CASE 
                    WHEN a.assettype = 'f625b904-befc-4685-9dd8-15a20b23a58b' THEN 'LGC'
                    WHEN a.assettype = '6c1883d1-7e50-441a-854c-b53552001e5f' THEN 'OTL'
                END AS otl_vs_lgc
            FROM assets a
            LEFT JOIN attribuutwaarden aw 
                ON a.uuid = aw.assetuuid 
                AND aw.attribuutuuid IN (
                    'ce1d97ff-40bb-47b3-ac27-b491c9c52e71',  -- Legacy Segment controller serienummer
                    '18886613-e51d-49b6-a62d-f0dbef85080e'   -- Segmentcontroller serienummer
                )
            WHERE a.actief IS TRUE 
                AND a.assettype IN (
                    'f625b904-befc-4685-9dd8-15a20b23a58b', -- Legacy
                    '6c1883d1-7e50-441a-854c-b53552001e5f'  -- OTL
                )
                AND aw.waarde IS NOT NULL
                AND aw.waarde !~ '^APS-G3-\d{4}-\d{3}$'
        )
        SELECT *
        FROM cte_segmentcontroller
        ORDER BY naam, otl_vs_lgc;
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
