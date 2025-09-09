from DQReport import DQReport


class Report0199:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0199',
                               title='Seinbrug is een punt',
                               spreadsheet_id='1hxBCVXI5mTzZ9Xc6sz6nBRtnNMWVZ-lDslutSIw1UOs',
                               datasource='PostGIS',
                               persistent_column='E',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_seinbrug as (
                select
                    a.uuid
                    , a.naam
                    , st_astext(g.geometry) as geometry
                    , st_geometrytype(g.geometry) as "geometry_type"
                    , ST_area(g.geometry) as "oppervlakte"	
                from assets a
                left join geometrie g on a."uuid" = g.assetuuid 
                where a.assettype = '40b2e487-f4b8-48a2-be9d-e68263bab75a'  -- Seinbrug
                 and a.actief is true
                order by st_area(g.geometry) desc
            )
            -- RSA-query
            select
                uuid, naam, geometry, oppervlakte
            from cte_seinbrug
            where
                geometry_type = 'ST_Point'
                or
                geometry_type = 'ST_Polygon' and oppervlakte <= 4
            order by oppervlakte desc
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
