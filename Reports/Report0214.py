from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0214(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET dnblaagspanning_key = (
  FOR at IN assettypes
    FILTER at.label == "DNBLaagspanning"
    LIMIT 1
    RETURN at._key
)

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.assettype_key == dnblaagspanning_key
  LET bevestiging = FIRST(
    FOR v, rel IN ANY a._id bevestiging_relaties
      LIMIT 1
      RETURN rel
  )
  FILTER bevestiging == null
  SORT a.AIMNaamObject_naam ASC
  RETURN {
    ls_uuid: a._key,
    ls_label: "DNBLaagspanning",
    ls_actief: a.AIMDBStatus_isActief,
    ls_naam: a.AIMNaamObject_naam,
    ls_naampad: a.NaampadObject_naampad,
    relatie: "Geen Bevestiging-relatie aanwezig"
  }
"""
        self.report = DQReport(name='report0214',
                               title='Laagspanning (LS) is nergens aan bevestigd',
                               spreadsheet_id='1VaF3IRiF5lFOkh_hK4_PvTqYanhiaRzvJX_lqmWbn3g',
                               datasource='ArangoDB',
                               persistent_column='G',
                               link_type='eminfra',
                               excel_filename='[RSA] Laagspanning (LS) is nergens aan bevestigd.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
