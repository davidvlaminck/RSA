from DQReport import DQReport


class Report0134:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0134',
                               title='Overlappende gebouwen',
                               spreadsheet_id='1_8Xqs3uVeOPrnWJfnOuXrDkuEzhC1TRd6ybWPKk3-m4',
                               datasource='PostGIS',
                               persistent_column='I'
                               )

        self.report.result_query = """
            /*
             * Gebouwen wiens geometrie overlapt
             * Gedeeltelijke of volledige overlap (1 op 1).
             * 
             * */
            with cte_gebouw AS (
                SELECT
                    a.uuid
                    , a.toestand
                    , a.actief
                    , a.toestand
                    , a.naam
                    , g.wkt_string
                    , ST_GeomFromText(g.wkt_string, 31370) as geom
                    , ROUND(st_area(st_geomfromtext(g.wkt_string, 31370))::numeric, 2) as oppervlakte
                    --, g.geom
                FROM assets a
                LEFT JOIN geometrie g ON a.uuid = g.assetuuid
                where
                    a.assettype = '21566546-01d5-40d5-93c7-ec77a00e5d48' -- Gebouw
                    and
                    a.actief = true
                    and
                    a.toestand = 'in-gebruik'
            )
            -- Main query
            select
                g1.uuid as uuid
                , g2.uuid as gebouw2_uuid
                , g1.naam as gebouw1_naam
                , g2.naam as gebouw2_naam
                , g1.oppervlakte as gebouw1_opp
                , g2.oppervlakte as gebouw2_opp
                , ROUND(100 * (st_area(st_intersection(g1.geom, g2.geom)) / g1.oppervlakte)::NUMERIC, 2) as overlap_percentage
                , case 
                    when st_area(st_intersection(g1.geom, g2.geom)) / g1.oppervlakte >= 0.95 then true -- Het overlap percentage bedraagt > 95 percent.
                    else false
                end as "gebouw_has_95_perc_overlap"
                -- Disable geom in the nightly Report
                --, g1.geom as gebouw1_geom
                --, g2.geom as gebouw2_geom
            from cte_gebouw g1
            inner join cte_gebouw g2 on st_intersects(g1.geom, g2.geom) -- inner join en geen left join!
                and
                g1.uuid <> g2.uuid 	-- Geen vergelijking van een gebouw met zichzelf
            order by g1.uuid, g2.uuid
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
