from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0189(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0189', title='Agent EMT_VHS (rol=toezichtsgroep) bevat geen assets (OTL)',
                               spreadsheet_id='1cTynPJ7ufAiVPJzIAt9qufDR8Mba2nMeyTjgI2mqrgc', datasource='PostGIS',
                               persistent_column='E', link_type='eminfra')

        self.report.result_query = """
        with cte_betrokkenerelatie as (
            select
                a.naam
                , b.*
            from betrokkenerelaties b
            inner join agents a on b.doeluuid = a.uuid and a.uuid = '90436e0e-5d77-427a-b6e4-fe5247c6aaa1'  --EMT_VHS
        )
        -- main query
        select
            a.uuid
            , at.naam as assettype
            , a.naam
            , a.naampad 
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        inner join cte_betrokkenerelatie b on a."uuid" = b.bronuuid
        where
            a.actief is true
        order by assettype asc;
	    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
