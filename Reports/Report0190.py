from lib.reports.DQReport import DQReport


class Report0190:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0190', title='Toezichtsgroep en Schadebeheerder zijn tegengesteld (Legacy)',
                               spreadsheet_id='1BI4q-FF97SAWPtvkDH6rVnNu1CBc3ddQp5bNfjZiO7U', datasource='PostGIS',
                               persistent_column='E', link_type='eminfra')

        self.report.result_query = """
            with cte_asset_extra_info as (
                select 
                    a."uuid" 
                    , at.naam 
                    , concat(i.voornaam, ' ', i.naam) as toezichter
                    , t.naam as "toezichtsgroep"
                    , s.naam as "schadebeheerder"
                from assets a
                inner join assettypes at on a.assettype = at."uuid" and at.uri ~* 'lgc'
                -- Schadebeheerder
                left join beheerders s on a.schadebeheerder = s."uuid"
                -- Toezichtsgroep (Legacy)
                left join toezichtgroepen t on a.toezichtgroep = t."uuid"
                left join identiteiten i on a.toezichter = i."uuid"
                where
                    a.actief is true
                    -- whitelist van schadebeheerders
                    and s.naam not in (
                        'AGENTSCHAP WEGEN EN VERKEER'
                        , 'Federale Politie - DRI - BIOPS'
                    )
            )
            select
                *
            from cte_asset_extra_info
            where
                -- toezichtsgroep Antwerpen
                toezichtsgroep = 'V&W-WA'
                and
                schadebeheerder not in (
                    'AFDELING WEGEN ANTWERPEN'
                    , 'District Antwerpen'
                    , 'District Brecht'
                    , 'District Geel'
                    , 'District Puurs'
                    , 'District Vosselaar'
                    , 'Stad Geel'
                    , 'THV Via Kempen'
                    )
                -- toezichtsgroep Limburg
                OR
                toezichtsgroep = 'V&W-WL'
                and
                schadebeheerder not in (
                    'AFDELING WEGEN LIMBURG'
                    , 'District Centraal - Limburg'
                    , 'District Oost - Limburg'
                    , 'District West - Limburg'
                    , 'District Zuid - Limburg'
                )
                -- toezichtsgroep Oost-Vlaanderen
                OR
                toezichtsgroep = 'V&W-WO'
                and
                schadebeheerder not in (
                    'AFDELING WEGEN OOST-VLAANDEREN'
                    , 'District Aalst'
                    , 'District Eeklo'
                    , 'District Gent'
                    , 'District Oudenaarde'
                    , 'District St-Niklaas'
                    , 'Gemeente Wortegem-Petegem'
                )
                -- toezichtsgroep Vlaams-Brabant
                OR
                toezichtsgroep = 'V&W-WVB'
                and
                schadebeheerder not in (
                    'AFDELING WEGEN VLAAMS BRABANT'
                    , 'District Aarschot'
                    , 'District Halle'
                    , 'District Vilvoorde-autosnelwegen'
                    , 'District Leuven'
                )
                -- toezichtsgroep West-Vlaanderen
                or
                toezichtsgroep = 'V&W-WW'
                and
                schadebeheerder not in (
                    'AFDELING WEGEN WEST-VLAANDEREN'
                    , 'Ag. Maritieme Dienstverlening en Kust'
                    , 'District Brugge'
                    , 'District Pittem'
                    , 'District Kortrijk'
                    , 'District Ieper'
                    , 'District Oostende'
                    , 'Gemeente Anzegem'
                    , 'Gemeente Avelgem'
                    , 'Gemeente Zonnebeke'
                    , 'LP KORTRIJK KUURNE LENDELEDE'
                    , 'Meulebeke'
                    , 'THV Via Brugge'
                )
                -- toezichtsgroep null
                or
                toezichtsgroep is null
            order by toezichtsgroep asc, schadebeheerder asc, naam asc;
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
