from DQReport import DQReport


class Report0182:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0183', title='Teletransmissieverbinding (TT) ODF met meerdere HoortBij-relaties naar een KabelnetToegang',
                               spreadsheet_id='1xrzVWW4K4InhtoDMF3ETxcbZSo1MmyUy4EtbAAoMEmY', datasource='PostGIS',
                               persistent_column='G', link_type='eminfra')

        self.report.result_query = """
        with 
        cte_assets_TT_ODF as (
            select a.*
            from assets a 
            where
                a.naam ~ '.ODF$'
                and
                a.assettype = '8c2c8fb4-9e64-467c-a7a2-a72e9dbcff48'  -- Teletransmissieverbinding (Legacy)
                and 
                a.actief is true
        )
        , cte_relaties_hoortbij as (
            select
                rel.*
            from assetrelaties rel
            where
                rel.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'  -- HoortBij
                and
                rel.actief is true
        )
        , cte_assets_kabelnettoegang as (
            select a.*
            from assets a 
            where
                a.assettype = 'c505b262-fe1f-42cb-970f-7f44487b24ec'  -- Kabelnettoegang
                and 
                a.actief is true
        )
        -- main query
        -- TT_ODF met meer dan 1 HoortBij-relatie
        select
            a.uuid
            , a.toestand
            , a.naampad
            , a.naam
            , count(a.uuid) as aantal_kabelnettoegangen
            , string_agg(concat('uuid: ', a2.uuid::text, ' naam: ', a2.naam::text), '; ') as kabelnettoegang_info
        from cte_assets_TT_ODF a
        left join cte_relaties_hoortbij rel on a.uuid = rel.doeluuid
        left join cte_assets_kabelnettoegang a2 on rel.bronuuid = a2."uuid" 
        where rel.uuid is not null
        group by a.uuid, a.toestand, a.naampad, a.naam
        having count(a.uuid) > 1
        order by aantal_kabelnettoegangen desc, a.naampad asc
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
