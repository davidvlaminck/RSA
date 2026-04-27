from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0225(BaseReport):
    def init_report(self) -> None:
        aql_query = """
/* Report0225: Elektrische Keuring heeft een bijlage */
LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)

/* Select assets, filter by assettype + active + locatie */
FOR a IN assets
  FILTER a.assettype_key == key_elektrische_keuring AND a.AIMDBStatus_isActief == true

  LET naam = a.AbstracteAanvullendeGeometrie_naam ? a.AbstracteAanvullendeGeometrie_naam : null
  
  LET keuringsdatum = a.KeuringObject_keuringsdatum ? a.KeuringObject_keuringsdatum : null
  LET resultaat = a.ElektrischeKeuring_resultaat ? a.ElektrischeKeuring_resultaat : null
  
  LET bestandsnaam = a.AbstracteAanvullendeGeometrie_bijlage && a.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_bestandsnaam ? a.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_bestandsnaam : null
  LET uri = a.AbstracteAanvullendeGeometrie_bijlage && a.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_uri ? a.AbstracteAanvullendeGeometrie_bijlage.DtcDocument_uri : null
  
  // geen bijlage
  FILTER uri == null 
  
  SORT naam asc
  
  RETURN {
    'assetId.identificator': a._key,
    toestand: a.toestand,
    naam: naam,
    keuringsdatum: keuringsdatum,
    resultaat: resultaat,
    bestandsnaam: bestandsnaam,
    uri: uri
  }
        """
        self.report = DQReport(name='report0225',
                               title='Elektrische Keuring heeft een bijlage',
                               spreadsheet_id='',
                               datasource='ArangoDB',
                               persistent_column='H',
                               excel_filename='[RSA] Elektrische Keuring heeft een bijlage.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
