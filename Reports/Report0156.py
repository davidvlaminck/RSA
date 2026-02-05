from lib.reports.DQReport import DQReport


class Report0156:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0156',
                               title='Assets met dubbele Betrokkene-relatie naar dezelfe rol',
                               spreadsheet_id='19CqxgnN3XzlVv6yIAi7Dh5JEykr0k-YBYNH4q4tcNu0',
                               datasource='PostGIS',
                               persistent_column='G'
                               )

        self.report.result_query = """
        -- Assets met meerdere identieke betrokkene-relaties met dezelfe rol
        with cte_asset_met_assettype as (
            select
                a.uuid
                , aty.naam as assettype_naam
            from assets a
            left join assettypes aty on a.assettype = aty.uuid
        )
        -- main query
        select
            b.bronassetuuid
            , a.assettype_naam
            , string_agg(b.doeluuid::text, ';' order by b.doeluuid) as doeluuid_agent_agg
            , string_agg(agn.naam, ';' order by agn.naam) as agents
            , b.rol
            , count(b.rol) as aantal_rollen
        from betrokkenerelaties b
        left join cte_asset_met_assettype a on b.bronassetuuid = a.uuid
        left join agents agn on b.doeluuid = agn.uuid
        where b.actief = true and b.bronassetuuid is not null
        group by b.bronassetuuid, b.rol, a.assettype_naam
        having count(b.rol) >= 2
        order by aantal_rollen desc
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
