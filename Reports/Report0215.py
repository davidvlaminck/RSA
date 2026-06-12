from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0215(BaseReport):
    def init_report(self) -> None:
        aql_query = """
FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  LET assettype = FIRST(
    FOR at IN assettypes
      FILTER at._key == a.assettype_key
      FILTER at.actief == false
      FILTER REGEX_TEST(at.uri, 'https://lgc.*')
      LIMIT 1
      RETURN at
  )
  FILTER assettype != null
  SORT assettype.uri ASC
  RETURN {
    uuid: a._key,
    asset_status: a.AIMDBStatus_isActief,
    naam: a.AIMNaamObject_naam,
    naampad: a.NaampadObject_naampad,
    uri: assettype.uri,
    label: assettype.label,
    assettype_status: assettype.actief
  }
"""
        self.report = DQReport(name='report0215',
                               title='Actieve assets (Legacy) wiens assettype inactief is',
                               spreadsheet_id='1gmrHAnR-t459u8jY9hfoidWo3hRWg7zRY6aRDSgW2lM',
                               datasource='ArangoDB',
                               persistent_column='H',
                               link_type='eminfra',
                               excel_filename='[RSA] Actieve assets (Legacy) wiens assettype inactief is.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
