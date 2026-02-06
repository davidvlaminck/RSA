from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0128(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0128',
                               title='Afstand tussen legacy en OTL-voorstelling van de asset "Mast" is aanvaardbaar',
                               spreadsheet_id='1037M4_aDq9pF3ntRZhClYEB_GZxAdz5b82qH5WaeZv0',
                               datasource='PostGIS',
                               persistent_column='F'
                               )

        self.report.result_query = """
        /*
         * Selecteer de lichtmasten die via een hoortBij-relatie verbonden zijn (lgc- en otl-voorstelling)
         * , en waarbij de afstand tussen beide > X meter
         * */
        WITH cte_geom_tabel AS (
            SELECT lgc.uuid AS lgc_uuid, otl.uuid AS otl_uuid, 
                ST_SetSRID(ST_Point(x, y), 31370) AS lgc_geom, 
                ST_SetSRID(ST_GeomFromText(wkt_string), 31370) AS otl_geom 
            FROM assets lgc 
                INNER JOIN locatie llgc ON lgc.uuid = llgc.assetuuid 
                INNER JOIN assetrelaties a ON lgc.uuid = a.doeluuid 
                    AND a.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2' -- HoortBij
                INNER JOIN assets otl ON otl.uuid = a.bronuuid 
                INNER JOIN geometrie gotl ON otl.uuid = gotl.assetuuid 
            WHERE lgc.actief = TRUE AND lgc.assettype = '4dfad588-277c-480f-8cdc-0889cfaf9c78' -- VPLMast
                AND otl.actief = TRUE AND otl.assettype = '478add39-e6fb-4b0b-b090-9c65e836f3a0' -- WVLichtmast
                ), 
        dist_tabel AS (
            SELECT *, ST_Distance(lgc_geom, otl_geom) AS distance FROM cte_geom_tabel)
        -- Selecteer de afstanden groter dan X
        select *
        from dist_tabel
        where distance >= 3000
        order by distance desc;
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
