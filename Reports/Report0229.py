from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0229(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /*
        Report0229: Laagspanningsbord overzicht
        
        Overzicht van de informatie gelinkt aan Laagspanningsborden: Elektrische Keuring; Agents; Locatie
        
        - Laagspanningsbord: uuid, naam, naampad
        - Elektrische Keuring: aantal, datum laatste keuring, resultaat keuring, naam van de bijlage
        - Agents: toezichter, toezichtsgroep, schadebeheerder
        - Locatie: provincie, gemeente, dichtstbijzijnde weglocatie, dichtstbijzijnde adres
        
        
        */
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        
        
        // Pre-compute the cardinality (number of assets per lsbord)
        LET lsbordCardinality = (
          FOR lsbord IN assets
            FILTER lsbord.assettype_key == key_laagspanningsbord AND lsbord.AIMDBStatus_isActief == true
            LET assetCount = LENGTH(
              FOR asset, edge IN 1..1 OUTBOUND lsbord assetrelaties
                FILTER edge.relatietype_key == key_relatie_heeftkeuring
                RETURN asset
            )
            RETURN { [lsbord._key]: assetCount }
        )
        LET lsbordCardinality_lookup = MERGE(lsbordCardinality)
        
        
        /* Alle Laagspanningsborden */
        FOR lsbord IN assets
          FILTER lsbord.assettype_key == key_laagspanningsbord and lsbord.AIMDBStatus_isActief == true
        
          // Filter for development
          // FILTER lsbord._key IN ['8a1a087d-9a07-458f-8274-82651fd6a6d6', 'f25db741-ba12-4515-ab4e-28cdaea19a3b'] 
        
          // Agent toezichter(s)
          LET agent_toezichters_array = (
            FOR agent_toezichter, edge_toezichter in 1..1 outbound lsbord betrokkenerelaties
              filter edge_toezichter.rol == 'toezichter'
              return agent_toezichter.purl.Agent_naam
            )
          LET agent_toezichters = CONCAT_SEPARATOR("; ", agent_toezichters_array)
            
          // Agent toezichtsgroep(en)
          LET agent_toezichtsgroepen_array = (
            FOR agent_toezichtsgroep, edge_toezichtsgroep in 1..1 outbound lsbord betrokkenerelaties
              filter edge_toezichtsgroep.rol == 'toezichtsgroep'
              return agent_toezichtsgroep.purl.Agent_naam
            )
          LET agent_toezichtsgroepen = CONCAT_SEPARATOR("; ", agent_toezichtsgroepen_array)
          
          // Agent schadebeheerder(s)
          LET agent_schadebeheerders_array = (
            FOR agent_schadebeheerder, edge_schadebeheerder in 1..1 outbound lsbord betrokkenerelaties
              filter edge_schadebeheerder.rol == 'schadebeheerder'
              return agent_schadebeheerder.purl.Agent_naam
            )
          LET agent_schadebeheerders = CONCAT_SEPARATOR("; ", agent_schadebeheerders_array)
        
          // Locatie
          // Locatie adres
          LET locatie = lsbord.loc.Locatie_puntlocatie != null ? lsbord.loc.Locatie_puntlocatie : null
          LET locatie_adres = locatie.DtcPuntlocatie_adres != null ? locatie.DtcPuntlocatie_adres : null
          LET locatie_adres_provincie = locatie_adres.DtcAdres_provincie != null ? locatie_adres.DtcAdres_provincie : null
          LET locatie_adres_gemeente = locatie_adres.DtcAdres_gemeente != null ? locatie_adres.DtcAdres_gemeente : null
          LET locatie_adres_straat = locatie_adres.DtcAdres_provincie != null ? locatie_adres.DtcAdres_straat : null
          LET locatie_adres_nummer = locatie_adres.DtcAdres_gemeente != null ? locatie_adres.DtcAdres_nummer : null
          LET locatie_adres_postcode = locatie_adres.DtcAdres_provincie != null ? locatie_adres.DtcAdres_postcode : null
          LET locatie_adres_compleet = CONCAT(
            locatie_adres_straat != null ? locatie_adres_straat: "",
            locatie_adres_nummer != null ? locatie_adres_nummer: "",
            locatie_adres_postcode != null ? locatie_adres_postcode: "",
            locatie_adres_gemeente != null ? locatie_adres_gemeente: ""
          )
          
          // Locatie weglocatie
          LET locatie_weglocatie = locatie.DtcPuntlocatie_weglocatie != null ? locatie.DtcPuntlocatie_weglocatie : null
          LET locatie_ident8 = locatie_weglocatie.DtcWeglocatie_ident8 != null ? locatie_weglocatie.DtcWeglocatie_ident8 : null
        
          /* LEFT JOIN: HeeftKeuring-relatie van Laagspanningsbord naar Elektrische Keuring (optional), cardinality > 1 */
          LET elektrische_keuringen = (
            FOR elek_keuring, edge2 IN 0..1 OUTBOUND lsbord assetrelaties
              FILTER elek_keuring.assettype_key == key_elektrische_keuring OR elek_keuring.assettype_key == null
              FILTER elek_keuring.AIMDBStatus_isActief == true OR elek_keuring.AIMDBStatus_isActief == null
              FILTER edge2.relatietype_key == key_relatie_heeftkeuring OR edge2.relatietype_key == null
              // Filter elektrische keuring met als toestand: in-gebruik
              FILTER elek_keuring.toestand == 'in-gebruik'
              
              // Sort by keuringsdatum in descending order (meest recente Elektrische Keuring eerst)
              SORT elek_keuring.KeuringObject_keuringsdatum desc
              
              RETURN {
                'assetId.identificator': elek_keuring._key,
                'typeURI': elek_keuring['@type'],
                'isActief': elek_keuring.AIMDBStatus_isActief,
                'toestand': SPLIT(elek_keuring.AIMToestand_toestand, '/')[-1],
                'naam': elek_keuring.AbstracteAanvullendeGeometrie_naam,
                'keuringsdatum': elek_keuring.KeuringObject_keuringsdatum,
                'resultaat': SPLIT(elek_keuring.ElektrischeKeuring_resultaat, '/')[-1],
                'eig_bijlage': elek_keuring.AbstracteAanvullendeGeometrie_bijlage,
                'eig_bijlage_uri': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_uri'] : null,
                'eig_bijlage_bestandsnaam': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_bestandsnaam'] : null,
                'eig_bijlage_omschrijving': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_omschrijving'] : null
                }
              )
          
          // Lookup the cardinality for the current lsbord
          LET elektrische_keuringen_aantal = length(elektrische_keuringen)
          //FILTER elektrische_keuringen_aantal >= 1
          // Lookup the cardinality for the current lsbord
          //LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
          //FILTER elektrische_keuringen_aantal == 0
          
          // Get the most recent Elektrische Keuring
          LET elektrische_keuring_laatste = LENGTH(elektrische_keuringen) >= 1 ? elektrische_keuringen[0] : null
          
          // Sort by provincie (asc), gemeente (asc), lsbordnaam (asc)
          SORT locatie_adres_provincie asc, locatie_adres_gemeente asc, lsbord.AIMNaamObject_naam asc
          
          RETURN {
            // lsbord
            'lsbord.assetId.identificator': lsbord._key,
            'lsbord.naam': lsbord.AIMNaamObject_naam,
            'lsbord.naampad': lsbord.NaampadObject_naampad,
            'lsbord.commentaar': lsbord.AIMObject_notitie,
            // info Agents
            'lsbord.toezichter_aantal': LENGTH(agent_toezichters_array),
            'lsbord.toezichter(s)': agent_toezichters,
            'lsbord.toezichtsgroep_aantal': LENGTH(agent_toezichtsgroepen_array),
            'lsbord.toezichtsgroep(en)': agent_toezichtsgroepen,
            'lsbord.schadebeheerder_aantal': LENGTH(agent_schadebeheerders_array),
            'lsbord.schadebeheerder(s)': agent_schadebeheerders,
            // info Locatie
            'lsbord.locatie_adres': locatie_adres_compleet,
            'lsbord.locatie_provincie': locatie_adres_gemeente,
            'lsbord.locatie_gemeente': locatie_adres_provincie,
            'lsbord.ident8': locatie_ident8,
            // # elektrische keuringen
            'elektrische_keuringen_aantal': elektrische_keuringen_aantal,
            // info Elektrische Keuring 
            'elektrische_keuring_meest_recent': elektrische_keuring_laatste,
            'elek_keuring.naam': elektrische_keuring_laatste.naam,
            'elek_keuring.keuringsdatum': elektrische_keuring_laatste.keuringsdatum,
            'elek_keuring.resultaat': elektrische_keuring_laatste.resultaat,
            'elek_keuring.eig_bijlage': elektrische_keuring_laatste.eig_bijlage,
            'elek_keuring.eig_bijlage_uri': elektrische_keuring_laatste.eig_bijlage_uri,
            'elek_keuring.eig_bijlage_bestandsnaam': elektrische_keuring_laatste.eig_bijlage_bestandsnaam,
            'elek_keuring.eig_bijlage_omschrijving': elektrische_keuring_laatste.eig_bijlage_omschrijving,
          }       
        """
        self.report = DQReport(name='report0229',
                               title='Laagspanningsbord overzicht',
                               spreadsheet_id='d72d5033-590b-45b9-84ec-9e458b610886',
                               datasource='ArangoDB',
                               persistent_column='X',
                               excel_filename='[RSA] Laagspanningsbord overzicht.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
