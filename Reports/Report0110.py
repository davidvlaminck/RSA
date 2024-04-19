from DQReport import DQReport


class Report0110:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0110', title='Geometrie is geldig: Open Geospatial Consortium standaard',
                               spreadsheet_id='1s8IdTaTSo0tMNKU59hTj5SgrJFt3bTG1DbidwFrXIv0', datasource='PostGIS',
                               persistent_column='D')

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
            , 'invalid geometry: ' || reason(st_isvaliddetail(geom)) as info
            , st_astext(location(st_isvaliddetail(geom))) as invalid_location
        from cte_geom
        where not st_isvalid(geom) 
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
