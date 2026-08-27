from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0227(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_laagspanningsdeel = FIRST(FOR at IN assettypes FILTER at.short_uri == 'lgc:installatie#LSDeel' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        LET key_relatie_gemigreerdnaar = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'GemigreerdNaar' LIMIT 1 RETURN rel_type._key)
        
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
          
          FILTER lsdeel_datum != null
          
          LET elektrische_keuringen_aantal = LENGTH(
            FOR e IN assetrelaties
              FILTER e._from == lsbord._id AND e.relatietype_key == key_relatie_heeftkeuring
              RETURN 1
          )
          
          FILTER elektrische_keuringen_aantal == 0
          
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
                               spreadsheet_id='38486b84-cb11-485d-a522-ec85f4633e34',
                               datasource='ArangoDB',
                               persistent_column='N',
                               excel_filename='[RSA] Laagspanningsdeel met eigenschap datumLaatsteKeuring heeft minstens een Elektrische Keuring.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
