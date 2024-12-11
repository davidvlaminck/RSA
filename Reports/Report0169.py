from DQReport import DQReport


class Report0169:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0169',
                               title='Seinbruggen zijn 90 graden geöriënteerd',
                               spreadsheet_id='1nJCGkb1-RbNkU6B7vNMM2p26pbIeToCBVkaD9LSP71Y',
                               datasource='PostGIS',
                               persistent_column='H'
                               )

        self.report.result_query = """
        with cte_asset_seinbrug as (
            select
                a.uuid
                , a.toestand
                , a.naam
                , g.geometry
                , case 
                    when st_geometrytype(geometry) = 'ST_LineString'
                    then degrees(ST_Azimuth(ST_PointN(geometry, 1), ST_PointN(geometry, -1)))
                    when st_geometrytype(geometry) = 'ST_Polygon'
                    then degrees(ST_Azimuth(ST_PointN(ST_ExteriorRing(geometry), 1), ST_PointN(ST_ExteriorRing(geometry), 2)))
                end AS orientatie
            from assets a
            left join geometrie g on a.uuid = g.assetuuid
            where
                a.actief = true
                and 
                a.assettype = '40b2e487-f4b8-48a2-be9d-e68263bab75a'  -- Seinbrug
        )
        -- hoofd query
        -- Filter op de oriëntatie van de eerste twee punten (veelvoud van 90).
        select
            *
            , st_geometrytype(geometry) as geometrie_type
            , st_npoints(geometry) as n_punten
        from cte_asset_seinbrug
        where
            orientatie::numeric % 90 = 0  -- Geen rest na deling door 90°
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
