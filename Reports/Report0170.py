from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0170(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0170',
                               title='Actieve assets hebben een inactieve parent-asset',
                               spreadsheet_id='1XHAWkGnKse2bmZth1d0PybcvyWNDO-cv3QjokT1aOic',
                               datasource='PostGIS',
                               persistent_column='I',
                               link_type='eminfra'
                               )

        self.report.result_query = """
        -- Start de zoekopdracht via de parent assets, want dit zijn er minder.
        -- Parent: selecteer inactieve assets en hun origineel naampad. 
        -- Child: selecteer actieve assets en hun parent-naampad.
        -- Join beide tussentabellen op basis van het parent naampad (inner join)
        with
        cte_asset_parent as (
            select
                a.*
            from assets a
            where
                a.actief is false
                and
                a.naampad is not null
        ), 
        cte_asset_child as (
            select
                (regexp_matches(a.naampad, '^(.*)/[^/]*$'))[1] as naampad_parent
                , a.*
            from assets a
            where
                a.actief is true
                and
                a.naampad is not null
        )
        -- main query
        select
            chi.uuid as child_asset_uuid
            , chi.actief as child_asset_actief
            , chi.toestand as child_asset_toestand
            , chi.naampad as child_asset_naampad
            , par.uuid as parent_asset_uuid
            , par.actief as parent_asset_actief
            , par.toestand as parent_asset_toestand
            , par.naampad as parent_asset_naampad
        from cte_asset_parent par
        inner join cte_asset_child chi on par.naampad = chi.naampad_parent
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
