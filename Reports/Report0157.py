from lib.reports.DQReport import DQReport


class Report0157:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0157',
                               title='Assets zonder geometrie gelinkt aan TV-Proximus Trafiroad (dossier: HVV.089; bestek: 2017-R3-043)',
                               spreadsheet_id='1CZFtjX0ANRfmEXc-6-ElJ-hgRuwY3FdHZBxeiJVKtxE',
                               datasource='PostGIS',
                               persistent_column='D'
                               )

        self.report.result_query = """
        with cte_bestekkoppeling as (
            select
                bko.assetuuid
                , bes.edeltadossiernummer
            from bestekken bes
            left join bestekkoppelingen bko on bes.uuid = bko.bestekuuid
            where bes.edeltadossiernummer = 'HVV.089'
        ), cte_assets_no_geom as (
            -- actieve assets zonder geometrie
            select
                a.*
                , at.label as at_label
                , coalesce(g.geometry, l.geometry) as geometry
            from assets a
            left join assettypes at on a.assettype = at.uuid
            left join geometrie g on a.uuid = g.assetuuid
            left join locatie l on a.uuid = l.assetuuid
            where
                a.actief = true 
                and 
                coalesce(g.geometry, l.geometry) is null
        )
        -- hoofd query alle assets
        select
            a.uuid
            , a.at_label
            , b.edeltadossiernummer
        from cte_bestekkoppeling b
        inner join cte_assets_no_geom a on b.assetuuid = a.uuid
        order by a.at_label
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
