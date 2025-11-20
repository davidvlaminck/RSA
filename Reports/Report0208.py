from DQReport import DQReport


class Report0208:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0208',
                               title='HSCabineLegacy (Legacy) heeft hoogstens één Hoogspanningsdeel via de Bevestiging-relatie',
                               spreadsheet_id='1HgSbC_isvc31OTyYNe7P9Co294HyKXcISXcO-2Y9wy4',
                               datasource='PostGIS',
                               persistent_column='G',
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
            cte_hscabine_hsdeel_duplicate as (
                select *
                from cte_hscabine_hsdeel
                where hscab_uuid in (
                    select hscab_uuid
                    from cte_hscabine_hsdeel
                    group by hscab_uuid
                    having count(*) > 1	
                )
            )
            -- main query
            select * from cte_hscabine_hsdeel_duplicate order by hscab_uuid
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
