from DQReport import DQReport


class Report0108:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0108', title='Geometrie is geldig: enkelvoudig punt, lijn of vlak',
                               spreadsheet_id='1glkACdbjMyh81DFyxuKpC1yNjDZeWjDH_kxAyw-TkY0', datasource='PostGIS',
                               persistent_column='F')

        self.report.result_query = """
            with cte_geom as (
            SELECT
                assetuuid
                , wkt_string
                , SUBSTRING("wkt_string" FROM '^(POINT Z|LINESTRING Z|POLYGON Z)') AS wkt_string_prefix
                , st_geomfromtext(wkt_string) as geom
            FROM geometrie
            WHERE 
                wkt_string IS NOT null
            ), cte_geom_multiparts as (
            select
                assetuuid
                , st_geometrytype(geom) as geometry_type
                , geom
            from cte_geom
            where wkt_string ~ '^MULTI.*$' 
            )
            select 
                g.assetuuid
                , g.geometry_type
                , st_numgeometries(geom) as aantal_delen 
                , at.naam
                , at.URI
            from cte_geom_multiparts g
            left JOIN assets a ON g.assetuuid = a.uuid
            LEFT JOIN assettypes at ON a.assettype = at.uuid
            where
                a.actief = 'true'
                and 
                at.URI !~ '^(https://grp.).*' -- Regular expression does not start with 
            order by at.uri;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
