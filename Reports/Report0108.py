from DQReport import DQReport


class Report0106:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0108', title='Geometrie is geldig: enkelvoudig punt, lijn of vlak',
                               spreadsheet_id='1glkACdbjMyh81DFyxuKpC1yNjDZeWjDH_kxAyw-TkY0', datasource='PostGIS',
                               persistent_column='C')

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
        select 
            assetuuid
        --	, wkt_string
        --	, geom
            , st_geometrytype(geom) as geometry_type
        from cte_geom
        where st_numgeometries(geom) > 1
        
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
