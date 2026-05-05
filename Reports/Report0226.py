from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0226(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /* Report0226: Elektrische Keuring heeft de eigenschappen: naam, keuringsdatum, resultaat */
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        
        /* Select assets, filter by assettype + active + locatie */
        FOR elek_keuring IN assets
          FILTER elek_keuring.assettype_key == key_elektrische_keuring AND elek_keuring.AIMDBStatus_isActief == true
        
          LET naam = elek_keuring.AbstracteAanvullendeGeometrie_naam ? elek_keuring.AbstracteAanvullendeGeometrie_naam : null
          
          LET keuringsdatum = elek_keuring.KeuringObject_keuringsdatum ? elek_keuring.KeuringObject_keuringsdatum : null
          LET resultaat = elek_keuring.ElektrischeKeuring_resultaat ? SPLIT(elek_keuring.ElektrischeKeuring_resultaat, '/')[-1] : null
          
          LET bestandsnaam = elek_keuring.AbstracteAanvullendeGeometrie_bijlage && elek_keuring.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_bestandsnaam ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_bestandsnaam : null
          LET uri = elek_keuring.AbstracteAanvullendeGeometrie_bijlage && elek_keuring.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_uri ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_uri : null
          
          // geen eigenschappen keuringsdatum en resultaat
          FILTER naam == null or keuringsdatum == null OR resultaat == null 
            /* Count null values for property1 and property2 */
          LET null_count = (
            (naam == null ? 1 : 0) +
            (keuringsdatum == null ? 1 : 0) +
            (resultaat == null ? 1 : 0)
          )
        
        
          
          FOR lsbord, edge IN 1..1 INBOUND elek_keuring assetrelaties
            FILTER lsbord.assettype_key == key_laagspanningsbord OR lsbord.assettype_key == null
            
            FOR agent_toezichter, edge_toezichter in 1..1 outbound lsbord betrokkenerelaties
              filter edge_toezichter.rol == 'toezichter'
            
            FOR agent_toezichtsgroep, edge_toezichtsgroep in 1..1 outbound lsbord betrokkenerelaties
              filter edge_toezichtsgroep.rol == 'toezichtsgroep'
          
            FOR agent_schadebeheerder, edge_schadebeheerder in 1..1 outbound lsbord betrokkenerelaties
              filter edge_schadebeheerder.rol == 'schadebeheerder'
              
                /* Sort by null_count in descending order */
              SORT lsbord.toestand, null_count DESC, lsbord.AIMNaamObject_naam
        
              RETURN {
                'elek_keuring.assetId.identificator': elek_keuring._key,
                'elek_keuring.toestand': elek_keuring.toestand,
                'elek_keuring.naam': naam,
                'elek_keuring.keuringsdatum': keuringsdatum,
                'elek_keuring.resultaat': resultaat,
                'elek_keuring.bestandsnaam': bestandsnaam,
                'elek_keuring.uri': uri,
                'lsbord.assetId.identificator': lsbord._key,
                'lsbord.toestand': lsbord.toestand,
                'lsbord.naam': lsbord.AIMNaamObject_naam,
                'lsbord.naampad': lsbord.NaampadObject_naampad,
                'lsbord.commentaar': lsbord.AIMObject_notitie,
                'lsbord.toezichter': agent_toezichter.purl.Agent_naam,
                'lsbord.toezichtsgroep': agent_toezichtsgroep.purl.Agent_naam,
                'lsbord.schadebeheerder': agent_schadebeheerder.purl.Agent_naam,
              }
        """
        self.report = DQReport(name='report0226',
                               title='Elektrische Keuring invulgraad van de eigenschappen',
                               spreadsheet_id='',
                               datasource='ArangoDB',
                               persistent_column='',
                               excel_filename='[RSA] Elektrische Keuring invulgraad van de eigenschappen.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
