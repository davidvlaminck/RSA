from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0109(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0109', title='Geometrie is geldig: geen opeenvolgende punten',
                               spreadsheet_id='1AmtcjAkh5H95O_lXtd4p_MHeoqFpQKQlIRfQk3MxGQ4', datasource='PostGIS',
                               persistent_column='G')

        self.report.result_query = """
            WITH cte_geometrie_dubbele_punten AS (
                SELECT
                    assetuuid,
                    wkt_string,
                    SUBSTRING("wkt_string" FROM '^[^ (]+') AS wkt_string_prefix,
                    geometry
                FROM
                    geometrie
                where
                    -- geen missing geometriën of multi-geometriën
                    ST_NumGeometries(geometry) = 1
                    and
                    st_geometrytype(geometry) in ('ST_LineString', 'ST_Polygon', 'ST_Point')
                    and
                    ST_NPoints(st_removerepeatedpoints(geometry)) <> ST_NPoints(geometry)
            )
            select 
                g.assetuuid
                , at.uri as typeURI
                , at.label as assettype
                , g.wkt_string_prefix
                , ST_NPoints(g.geometry) - ST_NPoints(st_removerepeatedpoints(g.geometry)) as aantal_dubbele_punten
                -- Aantal karakters afronden tot het maximaal toegelaten aantal karakters in Google Sheets: 50.000
                , left(wkt_string, 100) as wkt_string_afgerond
            FROM
                cte_geometrie_dubbele_punten g
            left join assets a on g.assetuuid = a.uuid
            left join assettypes at on a.assettype = at.uuid
            where
                a.actief = true -- Enkel de actieve assets
                and
                at.URI !~ '^(https://grp.).*' -- Regular expression does not start with 
            order by aantal_dubbele_punten desc
        	"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
