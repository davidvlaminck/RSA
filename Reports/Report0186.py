from DQReport import DQReport


class Report0186:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0186', title='Bevestigingsrelatie bestaat tussen PTVerwerkingseenheid en PTDemodulatoren',
                               spreadsheet_id='1wZ4Z9wNQG95zK_Bj5Z3d5jsHTfJWC9OrlvWJ4ulhVeM', datasource='PostGIS',
                               persistent_column='N', link_type='eminfra')

        self.report.result_query = """
        with cte_assets_PT as (
            -- PT: Personentransport
            select
                -- info over assets
                a.uuid, a.assettype, at.naam as assettype_naam, a.naam, a.commentaar
                -- info over bestek
                , bk.startdatum as bestek_startdatum
                , bk.einddatum as bestek_einddatum
                , b.edeltadossiernummer
                , b.edeltabesteknummer
                , b.aannemernaam
                -- info over geometry
                , g.geometry
            from assets a
            left join assettypes at on a.assettype = at.uuid
            left join geometrie g on a.uuid = g.assetuuid
            left join bestekkoppelingen bk on a.uuid = bk.assetuuid
            left join bestekken b on bk.bestekuuid = b.uuid
            where
                a.actief is true
                and
                a.assettype in (
                    '0390242b-4462-436b-bcfa-035f2ee72130', -- PT-verwerkingseenheid
                    'ba1e055e-6a83-4a1a-b613-5e93ecb0baab' -- PT-demodulatoren
            )
        )
        -- main query
        /*
         * PT-verwerkingseenheden zonder Bevestiging-relatie naar PR-demodulatoren
         * */
        select
            a1.uuid
            , a1.assettype_naam
            , a1.naam
            , st_astext(a1.geometry)
            , a2.uuid
            , a2.assettype_naam
            , st_astext(a2.geometry)
            , st_distance(a1.geometry, a2.geometry) as afstand_tussen_verwerkingseenheid_en_demodulator
        --    , a1.bestek_startdatum
        --    , a1.bestek_einddatum
        --    , a1.edeltadossiernummer
            , a1.edeltabesteknummer
            , a1.aannemernaam
            , replace(aw.waarde, '''', '"')::json->>'DtcAssetVersie.context' as assetVersie_context
            , replace(aw.waarde, '''', '"')::json->>'DtcAssetVersie.versienummer' as assetVersie_versienummer
            , replace(aw.waarde, '''', '"')::json->>'DtcAssetVersie.timestamp' as assetVersie_timestamp
        from cte_assets_PT a1
        left join attribuutwaarden aw on a1.uuid = aw.assetuuid and aw.attribuutuuid = 'b4a9a588-5643-44e6-b4d4-b8cdd6685f79' --AssetVersie
        left join assetrelaties rel on a1.uuid = rel.bronuuid and rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20' -- Bevestiging
        left join cte_assets_PT a2 on st_dwithin(a1.geometry, a2.geometry, 100) and a2.assettype = 'ba1e055e-6a83-4a1a-b613-5e93ecb0baab' -- PT-demodulatoren
        where
            a1.assettype = '0390242b-4462-436b-bcfa-035f2ee72130' -- PT-verwerkingseenheid
            and 
            rel.uuid is null
        order by assetversie_context
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
