from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0196(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0196',
                               title='Lichtmast heeft een locatie',
                               spreadsheet_id='1dgAGfvuGBCnW4oWXm0eUJMqSv6PXbbtAEEmNNUdOmwk',
                               datasource='PostGIS',
                               persistent_column='J',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a.uuid
                , a.toestand
                , a.actief
                , a.naam
                , a.naampad
                , a.commentaar 
                , g.geometry
                , br.rol
                , age.naam as naam_toezichter
            from assets a
            left join geometrie g on a.uuid = g.assetuuid
            left join betrokkenerelaties br on a."uuid" = br.bronassetuuid and br.actief is true and br.rol = 'toezichter'
            left join agents age on br.doeluuid = age."uuid" 
            where
                a.assettype = '8d9f83fa-0e19-47ec-902f-ac2c538dd6d9' -- Lichtmast
                and
                a.actief = true
                and
                g.geometry is null
                and
                -- whitelist mobiele trajectcontrole
                a.uuid not in (
                    'eaa33c8b-edae-4ae6-8e27-ec70124ec412'::uuid
                    , '824a9543-8fbf-4723-aa63-b36e62f4ca26'::uuid
                )
            order by
                a.naampad
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
