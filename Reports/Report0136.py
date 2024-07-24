from DQReport import DQReport


class Report0136:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0136',
                               title='Straatkolk heeft betrokkene relaties beheerder en verantwoordelijke-reiniging',
                               spreadsheet_id='1uYTd1vGSKMxxWbkbTjgpSo969ntXGj_-xXebBGXPdVY',
                               datasource='PostGIS',
                               persistent_column='G'
                               )

        self.report.result_query = """
            with cte_asset as (
                select
                    a.*
                    , at.uri as assettype_uri
                    , l.ident2, l.ident8
                from assets a
                left join locatie l on a.uuid = l.assetuuid
                left join assettypes at on a.assettype = at.uuid
                where
                    a.assettype = 'a5c7c355-c073-4f31-8e77-389c4b7a6a9e'  -- Straatkolk
                    and
                    a.actief = true
            )
            , cte_betrokkenerelaties_beheerder as (
                select *
                from betrokkenerelaties b
                where b.rol in ('beheerder') and b.actief = True
            )
            , cte_betrokkenerelaties_verantwoordelijke_reiniging as (
                select *
                from betrokkenerelaties b
                where b.rol in ('verantwoordelijke-reiniging') and b.actief = True
            )
            , cte_agents as (
                select *
                from agents
                where actief = true
                order by naam
            )
            -- Main query
            select
                a.uuid
                ,a.assettype_uri
                ,a.ident2
                ,a.ident8
                ,ag1.naam as "beheerder"
                ,ag2.naam as "verantwoordelijke-reiniging"
            from cte_asset a
            left join cte_betrokkenerelaties_beheerder b1 on a.uuid = b1.bronassetuuid
            left join cte_agents ag1 on b1.doeluuid = ag1.uuid
            left join cte_betrokkenerelaties_verantwoordelijke_reiniging b2 on a.uuid = b2.bronassetuuid
            left join cte_agents ag2 on b2.doeluuid = ag2.uuid
            -- De beheerder ontbreekt
            -- De beheerder is AWV (start met district) en de verantwoordelijke-reiniging ontbreekt. 
            where
                ag1.naam is null
                or
                lower(ag1.naam) ~ '^district' and ag2.naam is null
            order by ident2, ident8, ag1.naam, ag2.naam asc;
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
