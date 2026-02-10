from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0182(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0182', title='Teletransmissieverbinding (TT) ODF zonder enige HoortBij-relatie naar een KabelnetToegang',
                               spreadsheet_id='1cQ9yN9I9UT2BAtTAcOJmZkO-A2zuxdSu_9zkP1j5LMs', datasource='PostGIS',
                               persistent_column='H', link_type='eminfra')

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
        -- main query
        -- TT_ODF zonder enige HoortBij-relatie
        select
            a.uuid
            , a.toestand
            , a.naampad
            , a.naam
            , ST_Astext(coalesce(g.geometry, l.geometry)) as geometry
            , gem.gemeente
            , gem.provincie 
        from cte_assets_TT_ODF a
        left join geometrie g on a.uuid = g.assetuuid
        left join locatie l on a.uuid = l.assetuuid
        left join cte_relaties_hoortbij rel on a.uuid = rel.doeluuid
        left join gemeente gem on st_dwithin(l.geometry, gem.geom, 0)
        where rel.uuid is null
        
	    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
