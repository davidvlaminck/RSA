from DQReport import DQReport


class Report0109:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0109', title='Geometrie is geldig: geen opeenvolgende punten',
                               spreadsheet_id='1AmtcjAkh5H95O_lXtd4p_MHeoqFpQKQlIRfQk3MxGQ4', datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
            WITH cte_geom AS (
                SELECT
                    assetuuid,
                    wkt_string,
                    SUBSTRING("wkt_string" FROM '^[^ (]+') AS wkt_string_prefix,
                    st_geomfromtext(wkt_string) AS geom
                FROM
                    geometrie
                WHERE
                    wkt_string IS NOT NULL
            )
            select distinct
                assetuuid,
                wkt_string_prefix,
                wkt_string
            FROM
                cte_geom
            where
                ST_NPoints(st_removerepeatedpoints(geom)) <> ST_NPoints(geom)
        	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
