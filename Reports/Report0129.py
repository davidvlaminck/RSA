from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0129(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0129',
                               title='Geometrie Linestring heeft identieke eindpunten en bevat maximum 2 punten',
                               spreadsheet_id='1bLfrHp7ETT6ZJwWshIiZRG81ID58LqaADks2ymPY_mM',
                               datasource='PostGIS',
                               persistent_column='E'
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
            where g.wkt_string ~ '^LINESTRING*'
        )
        select
            uuid
            , assettype_label
            , left(st_astext(geom), 100) as wkt_geom_afgerond
            , npoints
        from cte_asset_of_interest
        where
            npoints = 2 -- Linestring consists of exactly 2 points
            and
            st_pointn(geom, 1) = st_pointn(geom, -1) -- Endpoints of the linestring are identical
        order by assettype_label asc
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
