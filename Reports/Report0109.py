from DQReport import DQReport


class Report0109:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0109', title='Geometrie is geldig: geen opeenvolgende punten',
                               spreadsheet_id='1AmtcjAkh5H95O_lXtd4p_MHeoqFpQKQlIRfQk3MxGQ4', datasource='PostGIS',
                               persistent_column='E')

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
                    wkt_string IS NOT null
                -- Remove multipart geometries from the query
                -- Compare the number with/without the Multiparts
            )
            select 
                assetuuid
                , wkt_string_prefix
                , ST_NPoints(geom) - ST_NPoints(st_removerepeatedpoints(geom)) as aantal_dubbele_punten
                -- Aantal karakters afronden tot het maximaal toegelaten aantal karakters in Google Sheets: 50.000
                , left(wkt_string, 50000) as wkt_string_afgerond
            FROM
                cte_geom
            where
                ST_NPoints(st_removerepeatedpoints(geom)) <> ST_NPoints(geom)
            order by aantal_dubbele_punten desc
        	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
