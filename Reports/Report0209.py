from DQReport import DQReport


class Report0209:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0209',
                               title='HSCabineLegacy (Legacy) onbtreekt een Bevestiging-relatie naar een Hoogspanning',
                               spreadsheet_id='1_z8fp2h6JCWdCAX5XozBuylPa2r-4CKlQkBKhd5OM9E',
                               datasource='PostGIS',
                               persistent_column='D',
                               link_type='eminfra')

        self.report.result_query = """
            with
            cte_hscabine as (
                select uuid, naam, naampad from assets where actief is true and assettype = '1cf24e76-5bf3-44b0-8332-a47ab126b87e'
            ),
            cte_hs as (
                select uuid, naam, naampad from assets where actief is true and assettype = '46dcd9b1-f660-4c8c-8e3e-9cf794b4de75'
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
            cte_hscabine_hs as (
                select
                    hscab.uuid as hscab_uuid
                    , hscab.naam as hscab_naam
                    , hscab.naampad as hscab_naampad
                    , hs.uuid as hs_uuid
                    , hs.naam as hs_naam
                    , hs.naampad as hs_naampad
                from cte_hscabine hscab
                inner join cte_bevestiging rel on hscab.uuid = rel.bronuuid
                inner join cte_hs hs on rel.doeluuid = hs."uuid"  
            ),
            cte_hscabine_bevestigingsrelatie_hs_ontbreekt as (
                select
                    hscab.uuid as hscab_uuid
                    , hscab.naam as hscab_naam
                    , hscab.naampad as hscab_naampad
                from cte_hscabine hscab
                where hscab."uuid" not in (
                    select hscab_uuid from cte_hscabine_hs 
                )
            )
            -- main query
            select * from cte_hscabine_bevestigingsrelatie_hs_ontbreekt order by hscab_uuid
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
