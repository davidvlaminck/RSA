from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0228(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_laagspanningsdeel = FIRST(FOR at IN assettypes FILTER at.short_uri == 'lgc:installatie#LSDeel' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type IN relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        LET key_relatie_gemigreerdnaar = FIRST(FOR rel_type IN relatietypes FILTER rel_type.naam == 'GemigreerdNaar' LIMIT 1 RETURN rel_type._key)
        
        FOR edge IN assetrelaties
          FILTER edge.relatietype_key == key_relatie_gemigreerdnaar
          FILTER CONTAINS(edge._from, "assets/")
          FILTER CONTAINS(edge._to, "assets/")
          LET lsdeel = DOCUMENT(edge._from)
          LET lsbord = DOCUMENT(edge._to)
          FILTER lsdeel != null AND lsdeel.assettype_key == key_laagspanningsdeel AND lsdeel.AIMDBStatus_isActief == false
          FILTER lsbord != null AND lsbord.assettype_key == key_laagspanningsbord AND lsbord.AIMDBStatus_isActief == true
          
          LET lsdeel_inspectie = lsdeel.ins ? lsdeel.ins : null
          LET lsdeel_datum = lsdeel_inspectie.EMObject_datumLaatsteKeuring ? lsdeel_inspectie.EMObject_datumLaatsteKeuring : null
          LET lsdeel_resultaatKeuring = lsdeel_inspectie.EMObject_resultaatKeuring ? lsdeel_inspectie.EMObject_resultaatKeuring : null
          FILTER lsdeel_datum != null AND lsdeel_resultaatKeuring != null
          
          LET elek_keuringen = (
            FOR e IN assetrelaties
              FILTER e._from == lsbord._id AND e.relatietype_key == key_relatie_heeftkeuring
              LET ek = DOCUMENT(e._to)
              FILTER ek != null AND ek.assettype_key == key_elektrische_keuring AND ek.AIMDBStatus_isActief == true
              RETURN ek
          )
          
          FILTER LENGTH(elek_keuringen) >= 1
          
          LET has_match = (
            FOR elek_keuring IN elek_keuringen
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
              FILTER datum_identiek AND resultaat_identiek
              RETURN 1
          )
          FILTER LENGTH(has_match) == 0
          
          FOR elek_keuring IN elek_keuringen
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
              'elektrische_keuringen_aantal': LENGTH(elek_keuringen),
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
                               excel_filename='[RSA] lgc#Laagspanningsdeel (inactief) en Elektrische Keuring hebben een identieke datum en identiek resultaat.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
