from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0213(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET dnblaagspanning_key = "b4ee4ea9"
LET wegkantkast_key = "c3601915"

FOR a1 IN assets
  FILTER a1.AIMDBStatus_isActief == true
  FILTER a1.assettype_key == dnblaagspanning_key
  FOR rel IN assetrelaties
    FILTER rel._from == CONCAT('assets/', a1._key)
    FILTER rel.relatietype_key == "3ff9"
    FILTER rel.actief == true
    LET a2 = DOCUMENT(rel._to)
    FILTER a2 != null
    FILTER a2.AIMDBStatus_isActief == true
    FILTER a2.assettype_key == wegkantkast_key
    LET at1 = FIRST(FOR at IN assettypes FILTER at._key == a1.assettype_key LIMIT 1 RETURN at)
    LET at2 = FIRST(FOR at IN assettypes FILTER at._key == a2.assettype_key LIMIT 1 RETURN at)
    SORT a1.NaampadObject_naampad ASC
    RETURN {
      ls_uuid: a1._key,
      ls_label: at1 ? at1.label : null,
      ls_actief: a1.AIMDBStatus_isActief,
      ls_naam: a1.AIMNaamObject_naam,
      ls_naampad: a1.NaampadObject_naampad,
      relatie: "Bevestiging-relatie aanwezig",
      kast_uuid: a2._key,
      kast_label: at2 ? at2.label : null,
      kast_actief: a2.AIMDBStatus_isActief,
      kast_naam: a2.AIMNaamObject_naam,
      kast_naampad: a2.NaampadObject_naampad
    }
"""
        self.report = DQReport(name='report0213',
                               title='Laagspanning (LS) is bevestigd aan een Kast (Legacy)',
                               spreadsheet_id='1JK1zb3RP-mwDgcbenxjfSAcbWjCrMaq0vluRdhKIwQs',
                               datasource='ArangoDB',
                               persistent_column='L',
                               link_type='eminfra',
                               excel_filename='[RSA] Laagspanning (LS) is bevestigd aan een Kast (Legacy).xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
