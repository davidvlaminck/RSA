from DQReport import DQReport


class Report0121:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0121',
                               title='Netwerkpoorten hebben een unieke naam',
                               spreadsheet_id='1QPnohwuI7ziIFU2wac_9ZbOcJWr20asu4gvsr0t3x3E',
                               datasource='PostGIS',
                               persistent_column='I',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_netwerkpoort_aantal as (
                select a.naam, unnest(array_agg(a.uuid)) as uuid, count(a.naam) as aantal 
                from assets a 
                where
                    a.assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' -- Netwerkpoort
                    and 
                    a.actief = true 
                group by a.naam
                having count(a.naam) > 1
                order by naam asc
            )
            , cte_attribuutwaarden_netwerkpoort_type as (
                select distinct *
                from attribuutwaarden
                where attribuutuuid in ('97977fa6-732b-4222-94fa-b9723945bd79') -- Netwerkpoort.type
            )
            , cte_attribuutwaarden_netwerkpoort_merk as (
                select distinct *
                from attribuutwaarden
                where attribuutuuid in ('6db57eb2-e3ea-461f-812b-2d8fae7c2b0f') --Netwerkpoort.merk
            )
            select
                a."uuid"
                , a.naam
                , a_aantal.aantal as dubbele_naam_aantal
                , attr_type.waarde as type
                , attr_merk.waarde as merk
                --, b.edeltadossiernummer as bestek_dossiernummer
                --, b.edeltabesteknummer  as bestel_besteknummer
                --, b.aannemernaam as bestek_aannemernaam
            from cte_netwerkpoort_aantal a_aantal
            left join assets a on a_aantal.uuid = a."uuid"
            left join cte_attribuutwaarden_netwerkpoort_type attr_type on a."uuid" = attr_type.assetuuid
            left join cte_attribuutwaarden_netwerkpoort_merk attr_merk on a."uuid" = attr_merk.assetuuid
            left join bestekkoppelingen bk on a.uuid = bk.assetuuid 
            left join bestekken b on bk.bestekuuid = b."uuid"
            where
                a.actief = true
                and
                a.assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' -- Netwerkpoort
            order by a.naam
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
