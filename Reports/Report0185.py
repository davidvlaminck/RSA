from DQReport import DQReport


class Report0185:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0185', title='IP Netwerkelementen hebben dezelfde locatie als hun Bijhorende legacy object van type IP',
                               spreadsheet_id='1cR7109F1_7iW0OVc65zMIOkAj-qUKH7S_Z012VIQP5U', datasource='PostGIS',
                               persistent_column='I', link_type='eminfra')

        self.report.result_query = """
        WITH cte_asset_netwerkelement AS (
            SELECT 
                a.uuid, 
                a.naam as netwerkelement_naam,
                coalesce(g.geometry, l.geometry) as geometry
            FROM 
                assets a
            left join geometrie g on a.uuid = g.assetuuid
            left join locatie l on a.uuid = l.assetuuid
            WHERE
                a.assettype = 'b6f86b8d-543d-4525-8458-36b498333416'  -- Netwerkelement
                AND a.actief = TRUE 
        )
        , cte_asset_IP as (
            select
                a.uuid, 
                a.naam as ip_naam,
                a.naampad as ip_naampad,
                coalesce(g.geometry, l.geometry) as geometry
            from
                assets a
            left join geometrie g on a.uuid = g.assetuuid
            left join locatie l on a.uuid = l.assetuuid
            where
                a.assettype = '5454b9b1-1bf4-4096-a124-1e3aeee725a2'
                and
                a.actief = true
        )
        , cte_relatie_hoortbij as (
            select
                rel.*
            from assetrelaties rel
            where
                rel.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'  -- HoortBij-relatie
                and
                rel.actief = true
        )
        -- main query
        select
            a1.*
            , a2.*
            , round(st_distance(a1.geometry, a2.geometry)::numeric, 2) as afstand
        from cte_asset_netwerkelement a1
        left join cte_relatie_hoortbij rel on a1.uuid = rel.bronuuid
        left join cte_asset_IP a2 on rel.doeluuid = a2.uuid
        where a1.geometry::text <> a2.geometry::text
        order by afstand desc
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
