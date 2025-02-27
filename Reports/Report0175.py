from DQReport import DQReport


class Report0175:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0175',
                               title='SegmentControllers (SegC (OTL) - [HoortBij] - SegC (LGC)) hebben identieke serienummers.',
                               spreadsheet_id='1qoXaCy5U2H-HloAHNojkuraN4Du1D0gWy6yr4nY2BjQ',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra'
                               )

        self.report.result_query = """
        with
        cte_asset_segmentcontroller_otl as (
            select
                a.*
                , attr.waarde as serienummer_otl
            from assets a
            left join attribuutwaarden attr on a.uuid = attr.assetuuid
            where
                a.actief is true
                and a.assettype = '6c1883d1-7e50-441a-854c-b53552001e5f'  -- Segmentcontroller
                and attr.attribuutuuid = '18886613-e51d-49b6-a62d-f0dbef85080e'  -- attribuut serienummer
        ),
        cte_asset_segmentcontroller_lgc as (
            select
                a.*
                , attr.waarde as serienummer_lgc
            from assets a
            left join attribuutwaarden attr on a.uuid = attr.assetuuid
            where
                a.actief is true
                and a.assettype = 'f625b904-befc-4685-9dd8-15a20b23a58b'  -- Segment controller (Legacy)
                and attr.attribuutuuid = 'ce1d97ff-40bb-47b3-ac27-b491c9c52e71'  -- attribuut serienummer
        ),
        cte_hoortbij_relaties as (
            select
                rel.*
            from assetrelaties rel
            where rel.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
            and rel.actief is true
        )
        /* segc_otl en segc_lgc */
        select
            segc_otl.uuid
            , segc_otl.naam
            , segc_otl.serienummer_otl
        	, segc_lgc.uuid
        	, segc_lgc.naam
        	, segc_lgc.serienummer_lgc
        from cte_asset_segmentcontroller_otl as segc_otl
        left join cte_hoortbij_relaties as rel on segc_otl.uuid = rel.bronuuid
        left join cte_asset_segmentcontroller_lgc as segc_lgc on rel.doeluuid = segc_lgc.uuid
        -- identical serienummers, implies a relation (Hoortbij) between OTL-asset and LGC-asset
        -- therefore, check only on identical serienummers
        where serienummer_otl <> coalesce(serienummer_lgc, '')
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
