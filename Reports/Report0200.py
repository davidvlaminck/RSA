from DQReport import DQReport


class Report0200:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0200',
                               title='Assets hebben foutieve toezichters',
                               spreadsheet_id='1A0CqgpEDRN0Zdet0QFQM8T90VFTpQ6_qL2GqHc9i3J0',
                               datasource='PostGIS',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_agents as (
                -- CTE met specifieke agents die niet meer als toezichter opereren
                select a.*
                from agents a 
                where a."uuid" in (
                    'cb7be547-0f62-4e6b-bb0e-f42d59bfe37d'  -- Martin Van Leuven
                    , 'bf1fa78e-c0fc-459d-82f5-369d3f4a704a'  -- Maurits Van Overloop
                )
            )
            -- main query
            select
                a."uuid"
                , a.actief
                , a.toestand 
                , a.naam 
                , age.naam as agent_naam
            from assets a
            left join assettypes at on a.assettype = at.uuid
            inner join betrokkenerelaties br on a."uuid" = br.bronassetuuid 
            inner join cte_agents age on br.doeluuid = age."uuid" 
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
