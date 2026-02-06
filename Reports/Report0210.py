from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0210(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0210',
                               title='HSCabineLegacy (Legacy) ontbreekt een Bevestiging-relatie naar een Hoogspanningsdeel',
                               spreadsheet_id='14djKCmoRIQsKSlcPb2oJCw-PoQfRn0oDqfj2QGtnqEU',
                               datasource='PostGIS',
                               persistent_column='D',
                               link_type='eminfra')

        self.report.result_query = """
        with
        cte_hscabine as (
            select uuid, naam, naampad from assets where actief is true and assettype = '1cf24e76-5bf3-44b0-8332-a47ab126b87e'
        ),
        cte_hsdeel as (
            select uuid, naam, naampad from assets where actief is true and assettype = 'a9655f50-3de7-4c18-aa25-181c372486b1'
        ),
        cte_bevestiging as (
            -- Bevestiging is een bidirectionele relatie,
            -- De tabel dupliceren met omgekeerde bron- en doel-relaties.
            select
                rel1.uuid, rel1.bronuuid, rel1.doeluuid
            from assetrelaties rel1
            where rel1.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'
              and rel1.actief is true
            union
            select
                rel2.uuid, rel2.doeluuid as bronuuid, rel2.bronuuid as doeluuid
            from assetrelaties rel2
            where rel2.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'
              and rel2.actief is true
        ),
        cte_hscabine_hsdeel as (
            select
                hscab.uuid as hscab_uuid
                , hscab.naam as hscab_naam
                , hscab.naampad as hscab_naampad
                , hsdeel.uuid as hsdeel_uuid
                , hsdeel.naam as hsdeel_naam
                , hsdeel.naampad as hsdeel_naampad
            from cte_hscabine hscab
            inner join cte_bevestiging rel on hscab.uuid = rel.bronuuid
            inner join cte_hsdeel hsdeel on rel.doeluuid = hsdeel."uuid"  
        ),
        cte_hscabine_bevestigingsrelatie_hsdeel_ontbreekt as (
            select
                hscab.uuid as hscab_uuid
                , hscab.naam as hscab_naam
                , hscab.naampad as hscab_naampad
            from cte_hscabine hscab
            where hscab."uuid" not in (
                select hscab_uuid from cte_hscabine_hsdeel
            )
        )
        -- main query
        select * from cte_hscabine_bevestigingsrelatie_hsdeel_ontbreekt order by hscab_uuid
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
