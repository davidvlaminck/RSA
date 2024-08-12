from DQReport import DQReport


class Report0137:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0137',
                               title='Bijhorende assets hebben een verschillende toezichtshouder/toezichtsgroep',
                               spreadsheet_id='1HBOnmY6Q7ed3zeRMVlVL7EC6S9PiMa6gv80AWcdrve8',
                               datasource='PostGIS',
                               persistent_column='S'
                               )

        self.report.result_query = """
            -- HoortBij-relaties
            with cte_relatie_hoortbij as (
                select
                    r.bronuuid
                    , r.doeluuid
                from assetrelaties r 
                where
                    r.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
                    and
                    r.actief = True
            ), 
            -- OTL-asset met toezichthouder
            -- Toezichthouder via koppeltabel betrokkenerelatie met agents
            cte_asset_otl as (
                select
                    a.uuid as otl_uuid
                    --, a.naampad as otl_naampad
                    , a.naam as otl_naam
                    , at.uri as otl_uri
                    --, at.definitie as otl_definitie
                    , ag.naam as otl_betrokkene_naam
                    --, ag.contact_info as otl_betrokkene_contact_info
                    , ag.ovo_code as otl_betrokkene_ovo_code
                from assets a
                inner join assettypes at on a.assettype = at.uuid
                left join betrokkenerelaties b on a.uuid = b.bronassetuuid  -- of b.bronuuid
                left join agents ag on b.doeluuid = ag.uuid
                where
                    at.uri ~ '^https://wegenenverkeer.data.vlaanderen.be.*'
                    and
                    a.actief is true
            ),
            -- Legacy-asset met toezichthouder
            -- Toezichthouder via toezichter en toezichtsgroep
            cte_asset_lgc as (
                select
                    a.uuid as lgc_uuid
                    , a.naampad as lgc_naampad
                    , a.naam as lgc_naam
                    , at.uri lgc_uri
                    , at.definitie as lgc_definitie
                    , i.naam as lgc_toezichthouder_naam
                    , i.voornaam as lgc_toezichthouder_voornaam
                    , i.gebruikersnaam as lgc_toezichthouder_gebruikersnaam
                    , t.naam as lgc_toezichtsgroep_naam
                    , t.typegroep as lgc_toezichtsgroep_typegroep
                    , t.referentie as lgc_toezichtsgroep_referentie
                from assets a
                inner join assettypes at on a.assettype = at.uuid
                left join identiteiten i on a.toezichter = i.uuid
                left join toezichtgroepen t on a.toezichtgroep = t.uuid
                where
                    at.uri ~ '^https://lgc.data.wegenenverkeer.be.*'
                    and
                    a.actief is true
            )
            -- main query:
            -- Legacy en OTL-assets die via HoortBij-relatie aan elkaar zijn gekoppeld en die een verschillende toezichthouder kennen.
            select
                concat('https://apps.mow.vlaanderen.be/awvinfra/ui/?asset=', rel.bronuuid) as otl_link_elisainfra
                , otl.*
                , concat('https://apps.mow.vlaanderen.be/eminfra/installaties/', rel.doeluuid) as lgc_link_eminfra
                , lgc.*
            from cte_relatie_hoortbij rel
            inner join cte_asset_lgc lgc on rel.doeluuid = lgc.lgc_uuid
            inner join cte_asset_otl otl on rel.bronuuid = otl.otl_uuid
            where
                otl.otl_betrokkene_naam != concat(lgc.lgc_toezichthouder_voornaam, ' ', lgc.lgc_toezichthouder_naam)
                and 
                otl.otl_betrokkene_naam != lgc.lgc_toezichtsgroep_naam
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
