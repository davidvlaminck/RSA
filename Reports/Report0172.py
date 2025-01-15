from DQReport import DQReport


class Report0172:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0172',
                               title='Assets zitten volledig omvat in een andere asset van hetzelfde assettype (donut)',
                               spreadsheet_id='1TfxlJgBUJvRS5xY29ZVIjqHD_2-jpXJrfY1VILuPJhk',
                               datasource='PostGIS',
                               persistent_column='E'
                               )

        self.report.result_query = """
        with cte_asset as (
            select
                a."uuid"
                , a.assettype
                , at.naam as assettype_naam
                , g.geometry
        --		, coalesce(g.geometry, l.geometry) as geometry
            from assets a
            left join geometrie g on a."uuid" = g.assetuuid
            left join locatie l on a."uuid" = l.assetuuid
            left join assettypes at on a.assettype = at.uuid
            where
                a.actief is true 
                and
                a.assettype not in (
                    'afdeacf2-c21a-4ac4-9ee7-70bebe794638' -- assettype: Aanvullende geometrie
                    , '3cb59344-1591-42fe-8d3f-5b9b8dd585f2' -- assettype: IMKL extra plan
                )
                and
        --		coalesce(g.wkt_string, l.geometrie) ~ '^POLYGON'
                g.wkt_string ~ '^POLYGON'
                and st_isvalid(g.geometry) = true
        )
        select
            a1.uuid
            , a2.uuid
            , a1.assettype_naam
        --    , a1.geometry
        --    , a2.geometry
            , ROW_NUMBER() OVER (PARTITION BY a1.assettype ORDER BY a1.uuid) AS counter_assettype
        from cte_asset a1
        left join cte_asset a2 on a1.geometry && a2.geometry and st_containsproperly(a1.geometry, a2.geometry)
        where
            a1.uuid <> a2.uuid
            and
            a1.assettype = a2.assettype  -- identical assettype
        order by a1.assettype
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
