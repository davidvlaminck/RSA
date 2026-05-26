from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport
import uuid


class Report0227(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /* 
        Report0227: lgc#Laagspanningsdeel (inactief) -[GemigreerdNaar]- Laagspanningsbord heeft minstens 1 Elektrische Keuring
        
        Ieder Laagspanningsdeel met een eigenschap Keuringsdatum dient op het andere uiteinde een Elektrische Keuring te hebben.
        
        Vertrekken vanuit het lgc@Laagspanningsdeel, via het gemigreerde Laagspanningsbord (OTL)
          Relatie(s) naar Elektrische Keuring toevoegen
          Het aantal relaties met een Elektrische Keuring tellen en info toevoegen
          
        lgc@Laagspanningsdeel (inactive) -[GemigreerdNaar]- Laagspanningsbord -[HeeftKeuring]- Elektrische Keuring 
        
        */
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_laagspanningsdeel = FIRST(FOR at IN assettypes FILTER at.short_uri == 'lgc:installatie#LSDeel' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        LET key_relatie_gemigreerdnaar = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'GemigreerdNaar' LIMIT 1 RETURN rel_type._key)
        
        
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
        
        /* Alle Laagspanningsdelen */
        FOR lsdeel in assets
          FILTER lsdeel.assettype_key == key_laagspanningsdeel and lsdeel.AIMDBStatus_isActief == false
          LET lsdeel_inspectie = lsdeel.ins ? lsdeel.ins : null
          LET lsdeel_datum = lsdeel_inspectie.EMObject_datumLaatsteKeuring ? lsdeel_inspectie.EMObject_datumLaatsteKeuring : null
          LET lsdeel_resultaatKeuring = lsdeel_inspectie.EMObject_resultaatKeuring ? lsdeel_inspectie.EMObject_resultaatKeuring : null
          
        //  LIMIT 1000
          FOR lsbord, edge IN 1..1 OUTBOUND lsdeel assetrelaties
            /* Alle Laagspanningsborden */
            FILTER edge.relatietype_key == key_relatie_gemigreerdnaar
            FILTER lsbord.assettype_key == key_laagspanningsbord and lsbord.AIMDBStatus_isActief == true
        
            // Lookup the cardinality for the current lsbord
            LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
            
            /*Laagspanningsdeel heeft een datum en Elektrische Keuringen */
            FILTER lsdeel_datum != null and elektrische_keuringen_aantal == 0
            
            SORT lsbord.AIMNaamObject_naam asc
          
            RETURN {
              'lsdeel.assetId.identificator': lsdeel._key,
              'lsdeel.status': lsdeel.AIMDBStatus_isActief,
              'lsdeel.toestand': lsdeel.toestand,
              'lsdeel.naam': lsdeel.AIMNaamObject_naam,
              'lsdeel.naampad': lsdeel.NaampadObject_naampad,
              'lsdeel.datum': lsdeel_datum,
              'lsdeel.resultaatKeuring': lsdeel_resultaatKeuring,
              'lsbord.assetId.identificator': lsbord._key,
              'lsbord.toestand': lsbord.toestand,
              'lsbord.naam': lsbord.AIMNaamObject_naam,
              'lsbord.naampad': lsbord.NaampadObject_naampad,
              'lsbord.commentaar': lsbord.AIMObject_notitie,
              'elektrische_keuringen_aantal': elektrische_keuringen_aantal,
            }
        """
        self.report = DQReport(name='report0227',
                               title='Laagspanningsdeel met eigenschap datumLaatsteKeuring heeft minstens een Elektrische Keuring',
                               spreadsheet_id=str(uuid.uuid4()),
                               datasource='ArangoDB',
                               persistent_column='N',
                               excel_filename='[RSA] Laagspanningsdeel met eigenschap datumLaatsteKeuring heeft minstens een Elektrische Keuring.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
