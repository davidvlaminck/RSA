from lib.reports.DQReport import DQReport


class Report0158:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0158',
                               title='EAN-opzoeklijst',
                               spreadsheet_id='1C-nlhzivdGGKy4dETP9cYvpHGn1gcQSRLCetZ3vbNDo',
                               datasource='PostGIS',
                               persistent_column='V'
                               )

        self.report.result_query = """
            with cte_asset_ean_via_elek_aansluitkenmerk as (
                -- Assets waarbij EAN via het elektrisch aansluitkenmerk is ingevuld: # 2809 assets
                select
                    a.uuid as asset1_uuid	
                    , '' as asset2_uuid
                    , a.toestand as asset1_toestand
                    , '' as asset2_toestand
                    , a.actief::text as asset1_actief
                    , null as asset2_actief
                    , a.naampad as asset1_naampad
                    , '' as asset2_naampad
                    , a.naam as asset1_naam
                    , '' as asset2_naampad
                    , a.commentaar as asset1_commentaar
                    , '' as asset2_commentaar
                    , case 
                        when typ.uri ~ 'https://wegenenverkeer.data.vlaanderen.be.*' then 'OTL'
                        when typ.uri ~ 'https://lgc.data.wegenenverkeer.be.*' then 'LGC'
                        else 'Other'
                    end as asset1_assettype
                    , '' as asset2_assettype
                    , typ.uri as asset1_assettype_uri
                    , '' as asset2_assettype_uri
                    , typ.naam as asset1_assettype_naam
                    , '' as asset2_assettype_naam
                    , ea.ean as asset1_ean
                    , '' as asset2_ean
            --		, ea.aansluiting as aansluitkenmerk_aansluiting
                    , 1 as priority
                from assets a
                inner join elek_aansluitingen ea on a.uuid = ea.assetuuid
                left join assettypes typ on a.assettype = typ.uuid
                where
                    a.actief = true
            ),
            cte_asset_ean_via_OTL_attribuut as (
                -- Assets waarbij via het kenmerk (eigenschap) "EAN" een waarde is ingevuld: # 4919
                select 
                    a.uuid as asset1_uuid
                    , '' as asset2_uuid
                    , a.toestand as asset1_toestand
                    , '' as asset2_toestand
                    , a.actief::text as asset1_actief
                    , '' as asset2_actief
                    , a.naampad as asset1_naampad
                    , '' as asset2_naampad
                    , a.naam as asset1_naam
                    , '' as asset2_naam
                    , a.commentaar as asset1_commentaar
                    , '' as asset2_commentaar
                    , case 
                        when typ.uri ~ 'https://wegenenverkeer.data.vlaanderen.be.*' then 'OTL'
                        when typ.uri ~ 'https://lgc.data.wegenenverkeer.be.*' then 'LGC'
                        else 'Other'
                    end as asset1_assettype
                    , '' as asset2_assettype
                    , typ.uri as asset1_assettype_uri
                    , '' as asset2_assettype_uri
                    , typ.naam as asset1_assettype_naam
                    , '' as asset2_assettype_naam
                    , att.waarde as asset1_ean
                    , '' as asset2_ean
                    , 3 as priority
                from assets a
                inner join attribuutwaarden att on a.uuid = att.assetuuid
                left join assettypes typ on a.assettype = typ.uuid
                where
                    a.actief = true 
                    and
                    att.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698'  -- EAN
                    and 
                    att.waarde is not null
            ),
            cte_asset_via_HoortBij_relatie as (
                -- zodra de ean-waarde van de OTL-eigenschap is ingevuld, zoek naar een Legacy-asset via een HoortBij-relatie: # 558 
                select 
                    a1.asset1_uuid as asset1_uuid
                    , a2.uuid::text as asset2_uuid
                    , a1.asset1_toestand as asset1_toestand
                    , a2.toestand as asset2_toestand
                    , a1.asset1_actief as asset1_actief
                    , a2.actief::text as asset2_actief
                    , a1.asset1_naampad as asset1_naampad
                    , a2.naampad as asset2_naampad
                    , a1.asset1_naam as asset1_naam
                    , a2.naam as asset2_naam
                    , a1.asset1_commentaar as asset1_commentaar
                    , a2.commentaar as asset2_commentaar
                    , a1.asset1_assettype
                    , case 
                        when typ.uri ~ 'https://wegenenverkeer.data.vlaanderen.be.*' then 'OTL'
                        when typ.uri ~ 'https://lgc.data.wegenenverkeer.be.*' then 'LGC'
                        else 'Other'
                    end as asset2_assettype
                    , a1.asset1_assettype_uri
                    , typ.uri as asset2_assettype_uri
                    , a1.asset1_assettype_naam
                    , typ.naam as asset2_assettype_naam
                    , a1.asset1_ean
                    , ea.ean as asset2_ean
                    , 2 as priority
                from cte_asset_ean_via_OTL_attribuut a1
                left join assetrelaties rel on a1.asset1_uuid = rel.bronuuid -- of doeluuid?
                left join assets a2 on rel.doeluuid = a2.uuid
                inner join elek_aansluitingen ea on a2.uuid = ea.assetuuid
                left join assettypes typ on a2.assettype = typ.uuid		
                where
                    a2.actief = true
            )
            -- hoofd query
            /*
             * Er zijn 3 CTE-queries. Gebruik volgende voorrangsregels:
             *   cte_asset_ean_via_elek_aansluitkenmerk
             *   cte_asset_via_HoortBij_relatie
             *   cte_asset_ean_via_OTL_attribuut
             * 
             *   # 7728 (unieke assets)
             *   # 8286 (dubbele assets)
             * */
            SELECT 
            --	distinct on (asset1_uuid)  -- Behoud enkel 1 unieke record voor een asset_uuid.
                * 
            FROM (
                SELECT * FROM cte_asset_ean_via_elek_aansluitkenmerk
                UNION all -- Use UNION ALL to keep all records and prioritize later
                SELECT * FROM cte_asset_ean_via_OTL_attribuut
                union all 
                SELECT * FROM cte_asset_via_HoortBij_relatie
            ) all_cte_records
            ORDER BY asset1_uuid, priority;        
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
