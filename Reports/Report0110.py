from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0110(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0110', title='Geometrie is geldig: Open Geospatial Consortium standaard',
                               spreadsheet_id='1s8IdTaTSo0tMNKU59hTj5SgrJFt3bTG1DbidwFrXIv0', datasource='PostGIS',
                               persistent_column='E')

        self.report.result_query = """
            with cte_asset as (
                        SELECT
                            a.uuid
                            , at.label as assettype
                            , coalesce(g.wkt_string, l.geometrie) as wkt_string
                            , coalesce(g.geometry, l.geometry) as geometry
                        FROM assets a
                        left join geometrie g on a.uuid = g.assetuuid
                        left join locatie l on a.uuid = l.assetuuid
                        left join assettypes at on a.assettype = at.uuid
                        where
                            a.actief is true
                        )
            select
                uuid
                , assettype
                , 'invalid geometry: ' || reason(st_isvaliddetail(geometry)) as info
                , SUBSTRING("wkt_string" FROM '^(POINT Z|LINESTRING Z|POLYGON Z)') AS wkt_string_prefix
            from cte_asset
            where
            not st_isvalid(geometry)
	        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
