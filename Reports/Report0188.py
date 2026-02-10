from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0188(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0188', title='Toezichtsgroep EMT_VHS bevat geen assets (Legacy)',
                               spreadsheet_id='1PvWx9ksfXI0iUemdm_tI0gs2t4EfhVQtZXsFf4M_cqs', datasource='PostGIS',
                               persistent_column='G', link_type='eminfra')

        self.report.result_query = """
        with cte_toezichtsgroep as (
            select
                t.uuid, t.naam
            from toezichtgroepen t
            where t.uuid in (
                '032cd5a7-845a-4cf9-977c-43f025d44dd0'  -- EMT_VHS
            )
        )
        -- main query
        select
            a."uuid"
            , at.naam as assettype
            , a.naampad 
            , a.naam 
            , a.actief 
            , t.naam
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        inner join cte_toezichtsgroep t on a.toezichtgroep = t.uuid
        where a.actief is true
        order by assettype asc;
	    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
