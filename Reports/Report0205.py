from lib.reports.DQReport import DQReport


class Report0205:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0205',
                               title='Kast (Legacy) ontbreekt een Bevestiging-relatie naar een Laagspanning',
                               spreadsheet_id='1QCPpgI_7lIrA5dC4CwI1igOLiprs-3Ou-W_2N_wHkqI',
                               datasource='PostGIS',
                               persistent_column='D',
                               link_type='eminfra')

        self.report.result_query = """
            with
            cte_kast as (
                select uuid, naam, naampad from assets where actief is true and assettype = '10377658-776f-4c21-a294-6c740b9f655e'
            ),
            cte_ls as (
                select uuid, naam, naampad from assets where actief is true and assettype = '80fdf1b4-e311-4270-92ba-6367d2a42d47'
            ),
            cte_lsdeel as (
                select uuid, naam, naampad from assets where actief is true and assettype = 'b4361a72-e1d5-41c5-bfcc-d48f459f4048'
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
            cte_kast_ls as (
                select
                    k.uuid as k_uuid
                    , k.naam as k_naam
                    , k.naampad as k_naampad
                    , ls.uuid as ls_uuid
                    , ls.naam as ls_naam
                    , ls.naampad as ls_naampad
                from cte_kast k
                inner join cte_bevestiging rel on k.uuid = rel.bronuuid
                inner join cte_ls ls on rel.doeluuid = ls."uuid"  
            ),
            cte_kast_bevestigingsrelatie_ls_ontbreekt as (
                select
                    k.uuid as k_uuid
                    , k.naam as k_naam
                    , k.naampad as k_naampad
                from cte_kast k
                where k."uuid" not in (
                    select k_uuid from cte_kast_ls 
                )
            )
            -- main query
            select * from cte_kast_bevestigingsrelatie_ls_ontbreekt order by k_uuid
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
