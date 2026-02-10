from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0113(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0113', title='Dubbele geometrie - Galgpaal',
                               spreadsheet_id='1QpiwBAmNRIi-GP4EDfIUxMI_LV-qMMnjwzzaYk-ZoBc', datasource='PostGIS',
                               persistent_column='J')

        self.report.result_query = """
        with cte_asset_galgpaal as (
            select
                a.uuid
                , a.toestand
                , a.naam
                , a.commentaar
                , g.geometry
            from assets a
            left join geometrie g on a.uuid = g.assetuuid
            where
                a.actief is true 
                and
                a.assettype = '615356ae-64eb-4a7d-8f40-6e496ec5b8d7'  -- Galgpaal
        )
        select	
            a1.uuid as g1_uuid
            , a1.toestand as g1_toestand
            , a1.naam as g1_naam
            , a1.commentaar as g1_commentaar
            , a2.uuid as g2_uuid
            , a2.toestand as g2_toestand
            , a2.naam as g2_naam
            , a2.commentaar as g2_commentaar
            , round(ST_Distance(a1.geometry, a2.geometry)::numeric, 2) as afstand
        from cte_asset_galgpaal a1
        --Join 2 Galgpalen binnen een afstand van 5 meter.
        --Dit is niet per se foutief, maar zo missen we ook de kleinste afstanden niet.
        left join cte_asset_galgpaal a2 on st_dwithin(a1.geometry, a2.geometry, 5)
        where
            a1.uuid <> a2.uuid  -- geen join van een Galgpaal met zichzelf
        order by afstand desc
	    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
