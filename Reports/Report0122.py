from DQReport import DQReport


class Report0122:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0122',
                               title='Netwerkpoorten hebben een naam',
                               spreadsheet_id='1kOEWxEfBVrft7bxM3F6YiQrNk3YFRXeZmr2edsvhuwQ',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_attribuutwaarden_netwerkpoort_type as (
                select *
                from attribuutwaarden
                where attribuutuuid in ('f8590b23-3fa5-4d3f-bc4c-c2591a8bf7c8', '97977fa6-732b-4222-94fa-b9723945bd79') -- Netwerkpoort.type
            )
            , cte_attribuutwaarden_netwerkpoort_merk as (
                select *
                from attribuutwaarden
                where attribuutuuid in ('6eb792f9-65e2-49a6-b899-b89f2313b0ed', '6db57eb2-e3ea-461f-812b-2d8fae7c2b0f') --Netwerkpoort.merk
            )
            select
                a."uuid"
                , a.naam
                , attr_type.waarde as type
                , attr_merk.waarde as merk
                , b.edeltadossiernummer as bestek_dossiernummer
                , b.edeltabesteknummer  as bestel_besteknummer
                , b.aannemernaam as bestek_aannemernaam
            from assets a
            left join cte_attribuutwaarden_netwerkpoort_type attr_type on a."uuid" = attr_type.assetuuid
            left join cte_attribuutwaarden_netwerkpoort_merk attr_merk on a."uuid" = attr_merk.assetuuid
            left join bestekkoppelingen bk on a.uuid = bk.assetuuid 
            left join bestekken b on bk.bestekuuid = b."uuid"
            where
                a.actief = true
                and
                a.naam is null
                and
                a.assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' -- Netwerkpoort
            order by uuid
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
