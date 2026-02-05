from lib.reports.DQReport import DQReport


class Report0174:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0174',
                               title='Assets van bepaalde assettypes hebben een unieke naam',
                               spreadsheet_id='103WXbUchfGVpKN0eGTHc1X8-PJSq5rf2Ydz6FhePGFs',
                               datasource='PostGIS',
                               persistent_column='E'
                               )

        self.report.result_query = """
        with cte_assettypes as (
            -- selection of assettypes.
            select *
            from assettypes at
            where
                at.uri ~ '^https://wegenenverkeer.data.vlaanderen.be'  -- OTL assets
                and
                -- assettypes for which we want to assess if they have duplicate names
                at.uuid in (
                    'c3601915-3b66-4bde-9728-25c1bbf2f374'  -- Wegkantkast
                    , '478add39-e6fb-4b0b-b090-9c65e836f3a0'  -- WVLichtmast
                    , 'e78ce094-565b-4e8c-a956-88c105367a4f'  -- WVConsole
                    , '929c6289-734f-4949-b5ce-30b05836c19c'  -- VerlichtingstoestelLED
                    , 'b4ee4ea9-edd1-4093-bce1-d58918aee281'  -- DNBLaagspanning
                )
        ),
        cte_assets_duplicate as (
            select
                a.assettype 
                , at.naam as assettype_naam
                , a.naam
                , count(*) as aantal
            from assets a 
            inner join cte_assettypes at on a.assettype = at."uuid"
            where
                a.actief is true
                and
                a.naam is not null
            group by a.assettype, at.naam, a.naam
            having count(*) >= 2
            order by a.assettype, at.naam asc, aantal desc
        )
        -- main query
        select
            a2.uuid
            , a1.assettype_naam
            , a1.naam
            , a1.aantal
        from cte_assets_duplicate a1
        left join assets a2 on
            a1.assettype = a2.assettype
            and
            a1.naam = a2.naam
        order by
            a1.assettype_naam
            , a1.naam
            , a1.aantal 
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
