from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0173(BaseReport):
    def init_report(self) -> None:
        aql_query = """
FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.NaampadObject_naampad == null OR a.NaampadObject_naampad == ""
  LET assettype = FIRST(
    FOR at IN assettypes
      FILTER at._key == a.assettype_key
      FILTER REGEX_TEST(at.uri, '^https://lgc.data.wegenenverkeer.be')
      LIMIT 1
      RETURN at
  )
  FILTER assettype != null
  SORT a.NaampadObject_naampad ASC, a.AIMNaamObject_naam ASC
  RETURN {
    uuid: a._key,
    toestand: a.toestand,
    actief: a.AIMDBStatus_isActief,
    naam: a.AIMNaamObject_naam,
    naampad: a.NaampadObject_naampad,
    assettype_naam: assettype.label,
    assettype_uri: assettype.uri
  }
"""
        self.report = DQReport(name='report0173',
                               title='Legacy assets ontbreken een naampad',
                               spreadsheet_id='1Lu1nSafM08GgwY1FHd4vnEN6qbS0Z4lI-H96gZzV8Z0',
                               datasource='ArangoDB',
                               persistent_column='H',
                               link_type='eminfra',
                               excel_filename='[RSA] Legacy assets ontbreken een naampad.xlsx',
                               )

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
