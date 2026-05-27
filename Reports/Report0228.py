from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0228(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /*
        Report0228: lgc#Laagspanningsdeel (inactief) en Elektrische Keuring hebben geen identieke datum en resultaat
        
        lgc@Laagspanningsdeel (inactive) -[GemigreerdNaar]- Laagspanningsbord -[HeeftKeuring]- Elektrische Keuring
        
        */
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_laagspanningsdeel = FIRST(FOR at IN assettypes FILTER at.short_uri == 'lgc:installatie#LSDeel' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type IN relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        LET key_relatie_gemigreerdnaar = FIRST(FOR rel_type IN relatietypes FILTER rel_type.naam == 'GemigreerdNaar' LIMIT 1 RETURN rel_type._key)
        
        /* Pre-compute the cardinality (number of assets per lsbord) */
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
        
        /* Find all lsdeel._key values where datum_identiek AND resultaat_identiek are true */
        LET lsdeel_keys_to_exclude = (
          FOR lsdeel IN assets
            FILTER lsdeel.assettype_key == key_laagspanningsdeel AND lsdeel.AIMDBStatus_isActief == false
            LET lsdeel_inspectie = lsdeel.ins ? lsdeel.ins : null
            LET lsdeel_datum = lsdeel_inspectie.EMObject_datumLaatsteKeuring ? lsdeel_inspectie.EMObject_datumLaatsteKeuring : null
            LET lsdeel_resultaatKeuring = lsdeel_inspectie.EMObject_resultaatKeuring ? lsdeel_inspectie.EMObject_resultaatKeuring : null
            FILTER lsdeel_datum != null AND lsdeel_resultaatKeuring != null
        
            FOR lsbord, edge IN 1..1 OUTBOUND lsdeel assetrelaties
              FILTER edge.relatietype_key == key_relatie_gemigreerdnaar
              FILTER lsbord.assettype_key == key_laagspanningsbord AND lsbord.AIMDBStatus_isActief == true
        
              LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
              FILTER elektrische_keuringen_aantal >= 1
        
              FOR elek_keuring, edge2 IN 1..1 OUTBOUND lsbord assetrelaties
                FILTER elek_keuring.assettype_key == key_elektrische_keuring AND elek_keuring.AIMDBStatus_isActief == true
                FILTER edge2.relatietype_key == key_relatie_heeftkeuring
        
                LET elek_keuring_datum = elek_keuring.KeuringObject_keuringsdatum ? elek_keuring.KeuringObject_keuringsdatum : null
                LET elek_keuring_resultaat = elek_keuring.ElektrischeKeuring_resultaat ? SPLIT(elek_keuring.ElektrischeKeuring_resultaat, '/')[-1] : null
        
                LET datum_identiek = (lsdeel_datum == elek_keuring_datum) ? true : false
                LET resultaat_identiek = (
                  (lsdeel_resultaatKeuring == elek_keuring_resultaat) OR
                  (lsdeel_resultaatKeuring == 'niet-conform met inbreuken' AND elek_keuring_resultaat == 'inbreuken') OR
                  (lsdeel_resultaatKeuring == 'conform met opmerkingen' AND elek_keuring_resultaat == 'conform-met-opmerkingen') OR
                  (lsdeel_resultaatKeuring == 'niet gekend' AND elek_keuring_resultaat == null) OR
                  (lsdeel_resultaatKeuring == 'geen keuring' AND elek_keuring_resultaat == null)
                ) ? true : false
        
                FILTER datum_identiek AND resultaat_identiek // both are true
                RETURN lsdeel._key
        )
        
        /* Alle Laagspanningsdelen */
        FOR lsdeel IN assets
          FILTER lsdeel.assettype_key == key_laagspanningsdeel AND lsdeel.AIMDBStatus_isActief == false
          /* Exclude lsdeel records where datum_identiek AND resultaat_identiek are true */
          FILTER NOT POSITION(lsdeel_keys_to_exclude, lsdeel._key)
        
          LET lsdeel_inspectie = lsdeel.ins ? lsdeel.ins : null
          LET lsdeel_datum = lsdeel_inspectie.EMObject_datumLaatsteKeuring ? lsdeel_inspectie.EMObject_datumLaatsteKeuring : null
          LET lsdeel_resultaatKeuring = lsdeel_inspectie.EMObject_resultaatKeuring ? lsdeel_inspectie.EMObject_resultaatKeuring : null
          FILTER lsdeel_datum != null AND lsdeel_resultaatKeuring != null
        
          FOR lsbord, edge IN 1..1 OUTBOUND lsdeel assetrelaties
            FILTER edge.relatietype_key == key_relatie_gemigreerdnaar
            FILTER lsbord.assettype_key == key_laagspanningsbord AND lsbord.AIMDBStatus_isActief == true
        
            LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
            FILTER elektrische_keuringen_aantal >= 1
        
            FOR elek_keuring, edge2 IN 1..1 OUTBOUND lsbord assetrelaties
              FILTER elek_keuring.assettype_key == key_elektrische_keuring AND elek_keuring.AIMDBStatus_isActief == true
              FILTER edge2.relatietype_key == key_relatie_heeftkeuring
        
              LET elek_keuring_datum = elek_keuring.KeuringObject_keuringsdatum ? elek_keuring.KeuringObject_keuringsdatum : null
              LET elek_keuring_resultaat = elek_keuring.ElektrischeKeuring_resultaat ? SPLIT(elek_keuring.ElektrischeKeuring_resultaat, '/')[-1] : null
        
              LET datum_identiek = (lsdeel_datum == elek_keuring_datum) ? true : false
              LET resultaat_identiek = (
                (lsdeel_resultaatKeuring == elek_keuring_resultaat) OR
                (lsdeel_resultaatKeuring == 'niet-conform met inbreuken' AND elek_keuring_resultaat == 'inbreuken') OR
                (lsdeel_resultaatKeuring == 'conform met opmerkingen' AND elek_keuring_resultaat == 'conform-met-opmerkingen') OR
                (lsdeel_resultaatKeuring == 'niet gekend' AND elek_keuring_resultaat == null) OR
                (lsdeel_resultaatKeuring == 'geen keuring' AND elek_keuring_resultaat == null)
              ) ? true : false
        
              SORT lsbord.AIMNaamObject_naam ASC
        
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
                'elek_keuring.assetId.identificator': elek_keuring._key,
                'elek_keuring.toestand': elek_keuring.toestand,
                'elek_keuring.naam': elek_keuring.AIMNaamObject_naam,
                'elek_keuring.commentaar': elek_keuring.AIMObject_notitie,
                'elek_keuring.datum': elek_keuring_datum,
                'elek_keuring.resultaatKeuring': elek_keuring_resultaat,
                'identieke datum': datum_identiek,
                'identiek resultaat': resultaat_identiek
              }
        """
        self.report = DQReport(name='report0228',
                               title='lgc#Laagspanningsdeel (inactief) en Elektrische Keuring hebben een identieke datum en identiek resultaat',
                               spreadsheet_id='88ecce1a-d98a-4b09-b790-181440833611',
                               datasource='ArangoDB',
                               persistent_column='V',
                               excel_filename='[RSA] lgc#Laagspanningsdeel (inactief) en Elektrische Keuring hebben een identieke datum en identiek resultaat')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
