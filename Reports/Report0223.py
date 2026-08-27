from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0223(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        
        FOR lsbord IN assets
          FILTER lsbord.assettype_key == key_laagspanningsbord and lsbord.AIMDBStatus_isActief == true
          LET elektrische_keuringen_aantal = LENGTH(
            FOR edge IN assetrelaties
              FILTER edge._from == lsbord._id AND edge.relatietype_key == key_relatie_heeftkeuring
              RETURN 1
          )
          FILTER elektrische_keuringen_aantal == 0
          
          SORT lsbord.AIMNaamObject_naam asc
        
          RETURN {
            'lsbord.assetId.identificator': lsbord._key,
            'lsbord.toestand': lsbord.toestand,
            'lsbord.naam': lsbord.AIMNaamObject_naam,
            'lsbord.naampad': lsbord.NaampadObject_naampad,
            'lsbord.commentaar': lsbord.AIMObject_notitie,
            'elektrische_keuringen_aantal': elektrische_keuringen_aantal,
          }
        """

        self.report = DQReport(name='report0223',
                               title='Laagspanningsbord heeft minstens 1 Elektrische Keuring',
                               spreadsheet_id='cce6f271-ee4f-4630-b283-ad2a62e34588',
                               datasource='ArangoDB',
                               persistent_column='G',
                               excel_filename='[RSA] Laagspanningsbord heeft minstens 1 Elektrische Keuring.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
