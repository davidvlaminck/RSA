from lib.reports.DQReport import DQReport


class Report0198:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0198',
                               title='Asset (OTL) heeft een inactieve toezichter',
                               spreadsheet_id='1c-dKxkczJRFVNEvNoXIem-HZ3e68Cx7yawfTg0rjNXg',
                               datasource='PostGIS',
                               persistent_column='J',
                               link_type='eminfra')

        self.report.result_query = """
            -- OTL: agents en betrokkenerelaties
            with cte_agent_inactief as (
                -- alle inactieve agents
                SELECT
                    br.uuid
                    , br.bronassetuuid
                    , br.doeluuid
                    , br.rol
                    , age.naam
                from agents age
                INNER JOIN betrokkenerelaties br ON age.uuid = br.doeluuid
                where age.actief is false
            )
            -- main query
            select
                a."uuid" 
                , at.uri
                , a.toestand 
                , a.actief
                , a.naampad 
                , a.naam 
                , a.commentaar 
                , age.naam as "naam_agent"
                , age.rol
            from assets a
            inner join cte_agent_inactief age on a.uuid = age.bronassetuuid
            left join assettypes at on a.assettype = at."uuid" 
            where a.actief is true
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
