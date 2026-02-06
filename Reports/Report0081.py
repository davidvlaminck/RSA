from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0081(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Verkeersregelaar\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND (
      a.AIMNaamObject_naam == null
      OR NOT (
        REGEX_TEST(a.AIMNaamObject_naam, "^\\d{3}[ACG]\\d.VR$")
        OR REGEX_TEST(a.AIMNaamObject_naam, "^W[WO]\\d{4}.VR$")
      )
    )
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0081',
                               title='Verkeersregelaars hebben als naam een conforme installatienummer',
                               spreadsheet_id='1v7sqt0OumZ0rEhRVFTwnl_4vNoWj3G0QSsUTKHxSOaE',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.naam is NULL OR NOT (a.naam =~ '^\\d{3}[ACG]\\d.VR$' OR a.naam =~ '^W[WO]\\d{4}.VR$')\nRETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
