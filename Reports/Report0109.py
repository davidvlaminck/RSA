from DQReport import DQReport


class Report0109:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0109', title='Geometrie is geldig: geen opeenvolgende punten',
                               spreadsheet_id='1AmtcjAkh5H95O_lXtd4p_MHeoqFpQKQlIRfQk3MxGQ4', datasource='PostGIS',
                               persistent_column='E')

        self.report.result_query = """
        with cte_geom as (
            SELECT
                assetuuid
                , wkt_string
                , SUBSTRING("wkt_string" FROM '^(POINT Z|LINESTRING Z|POLYGON Z)') AS wkt_string_prefix
                , st_geomfromtext(wkt_string) as geom
            FROM geometrie
            WHERE 
                wkt_string IS NOT NULL
            --limit 100000
        )
        SELECT
            assetuuid
            , wkt_string
        from cte_geom
        where 
            EXISTS (
                SELECT 1
                FROM (
                    SELECT
                        ST_Equals(ST_PointN(geom, i), ST_PointN(geom, i + 1)) AS is_duplicate
                    FROM
                        generate_series(1, ST_NumPoints(geom) - 1) AS i
                ) AS subquery
                WHERE is_duplicate
            )
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
