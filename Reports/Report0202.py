from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0202(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0202',
                               title='VPLMast (Legacy) heeft meerdere bijhorende WVLichtmast (OTL)',
                               spreadsheet_id='1shR393J5PkEGkIRgnoNr-jzFQrvcYKkzTdg2zPEiEqk',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_vplmast_hoortbij_wvlichtmast as (
                select
                    a1."uuid" as lgc_uuid
                    , SPLIT_PART(a1.naampad, '/', 1) AS installatie_naam
                    , a1.naampad as lgc_naampad
                    , a1.naam as lgc_naam
                    , a2."uuid" as otl_uuid
                    , a2."naam" as otl_naam
                from assets a1  -- VPLMast (Legacy)
                left join assetrelaties rel on a1."uuid" = rel.doeluuid 
                left join assets a2 on a2."uuid" = rel.bronuuid -- WVLichtmast (OTL)
                where
                    a1.assettype = '4dfad588-277c-480f-8cdc-0889cfaf9c78'  -- VPLMast (Legacy)
                    and
                    a1.actief is true
                    and
                    a2.assettype = '478add39-e6fb-4b0b-b090-9c65e836f3a0'  -- WVLichtmast (OTL)
                    and
                    a2.actief is true
                    and
                    rel.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'  -- Hoortbij
                order by
                    a1.uuid
            )
            -- main query
            select
                a.lgc_uuid
                , a.installatie_naam 
                , a.lgc_naampad
                , a.lgc_naam
                , count(a.lgc_uuid) as aantal_relaties
                , string_agg(a.otl_uuid::text, '; ') as otl_uuid
                , string_agg(a.otl_naam::text, '; ') as otl_naam
            from cte_vplmast_hoortbij_wvlichtmast a
            group by a.lgc_uuid, a.installatie_naam , a.lgc_naampad, a.lgc_naam
            having count(a.lgc_uuid) > 1
            order by a.installatie_naam asc, a.lgc_naam asc;
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
