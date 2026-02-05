from lib.reports.DQReport import DQReport


class Report0117:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0117',
                               title='DNBHoogspanning of DNBLaagspanning eanNummer stemt overeen met de legacy waarde. (dubbel)',
                               spreadsheet_id='1vqxb-Vjn-I25Iwy-xDihCPW3TOvPGsQR5d5aVjYZGnM',
                               datasource='PostGIS',
                               persistent_column='F')

        self.report.result_query = """
        with cte_assets_otl as (
        -- OTL assets met enkel uuid en waarde van het attribuut eanNummer
            select
                a.uuid
                , aw.waarde
            from assets a
            -- Join attribuutwaarde eanNummer 
            left join attribuutwaarden aw on a.uuid = aw.assetuuid
            where
                a.actief = true
                and
                -- Filter the assettype DNBHoogSpanning and DNBLaagSpanning
                (a.assettype = '8e9307e2-4dd6-4a46-a298-dd0bc8b34236'
                or
                a.assettype = 'b4ee4ea9-edd1-4093-bce1-d58918aee281')
                and
                aw.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698'
        ), cte_assets_lgc_aansluitingen as (
        -- Legacy asset
            select a.uuid, ea.ean as eanNummer, ea.aansluiting
            from elek_aansluitingen ea 
            left join assets a on ea.assetuuid = a."uuid"
            where a.actief = true
        ), cte_hoortBijRelaties as (
            select *
            from assetrelaties r 
            where r.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
            and actief = true
        )
        -- Main query: combineer legacy-asset en otl-asset op basis van de relatie 'HoortBij'
        -- In de assetrelatie is OTL gedocumenteerd als bron en legacy als doel
        select
            a_otl.uuid
            , a_otl.waarde as otl_waarde
            , a_lgc.uuid
            , a_lgc.eannummer as lgc_eannummer
            , a_lgc.aansluiting as lgc_aansluiting
        from cte_assets_otl a_otl
        left join cte_hoortBijRelaties r on a_otl.uuid = r.bronuuid
        left join cte_assets_lgc_aansluitingen a_lgc on r.doeluuid = a_lgc.uuid
        where a_lgc.eannummer is not null and a_otl.waarde != a_lgc.eanNummer
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
