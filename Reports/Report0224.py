from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0224(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /*
        Elektrische Keuring
        Vertrekken vanuit het Laagspanningsbord (OTL)
          Relatie(s) naar Elektrische Keuring toevoegen
          Het aantal relaties met een Elektrische Keuring tellen en info toevoegen.
          
        LEFT-JOIN toepassen, zodat alle Laagspanningsborden worden teruggegeven.
        
        Laagspanningsbord -[HeeftKeuring]- Elektrische Keuring 
        */
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        
        
        // Pre-compute the cardinality (number of assets per lsbord)
        LET lsbordCardinality = (
          FOR lsbord IN assets
            FILTER lsbord.assettype_key == key_laagspanningsbord
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
          LIMIT 100
        
          /* LEFT JOIN: HeeftKeuring-relatie van Laagspanningsbord naar Elektrische Keuring (optional), cardinality > 1 */
          LET elektrische_keuringen = (
            FOR elek_keuring, edge2 IN 0..1 OUTBOUND lsbord assetrelaties
              FILTER elek_keuring.assettype_key == key_elektrische_keuring OR elek_keuring.assettype_key == null
              FILTER elek_keuring.AIMDBStatus_isActief == true OR elek_keuring.AIMDBStatus_isActief == null
              FILTER edge2.relatietype_key == key_relatie_heeftkeuring OR edge2.relatietype_key == null
              
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
            LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
            FILTER elektrische_keuringen_aantal >= 1
            
            SORT elektrische_keuringen_aantal asc, lsbord.AIMNaamObject_naam asc
        
            RETURN {
              'lsbord.assetId.identificator': lsbord._key,
              'lsbord.naam': lsbord.AIMNaamObject_naam,
              'lsbord.naampad': lsbord.NaampadObject_naampad,
              'elektrische_keuringen_aantal': elektrische_keuringen_aantal,
              'elektrische_keuringen': elektrische_keuringen,
            }
        """
        self.report = DQReport(name='report0224',
                               title='Laagspanningsbord heeft meerdere Elektrische Keuringen met toestand in-gebruik',
                               spreadsheet_id='1',
                               datasource='ArangoDB',
                               persistent_column='')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
