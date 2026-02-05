from lib.reports.DQReport import DQReport


class Report0131:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0131',
                               title='Geometrie Polygoon heeft 3 of meer identieke punten en is visueel een punt.',
                               spreadsheet_id='1H2g6_SGcGPqRIDKxGavSQtZRFUCGpOddgvm6vJyxvEI',
                               datasource='PostGIS',
                               persistent_column='H'
                               )

        self.report.result_query = """
            with cte_asset_of_interest as (
                select
                    a.uuid
                    , at.label as assettype_label
                    , st_geomfromtext(g.wkt_string) as geom
                    , st_npoints(st_geomfromtext(g.wkt_string)) as npoints 
                from assets a
                left join geometrie g on a.uuid = g.assetuuid
                left join assettypes at on a.assettype = at.uuid
                where g.wkt_string ~ '^POLYGON*'
                  and at.uri !~ '^https://lgc.data.*'
            )
            select
                uuid
                , assettype_label
                , left(st_astext(geom), 100) as wkt_geom_afgerond
                , npoints
                , ST_PointN(ST_ExteriorRing(geom), 1) as vertex_1
                , ST_PointN(ST_ExteriorRing(geom), 2) as vertex_2
                , ST_PointN(ST_ExteriorRing(geom), ST_NumPoints(ST_ExteriorRing(geom))) as vertex_3    
            from cte_asset_of_interest
            where
                npoints = 3 -- Maximum of 3 points in polygon
                and
                st_pointn(ST_ExteriorRing(geom), 1) = ST_PointN(ST_ExteriorRing(geom), 2) -- All points are identical
            order by assettype_label asc;
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
