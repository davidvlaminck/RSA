from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0083(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Verkeersregelaar\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND (
      a.Verkeersregelaar_voltageLampen == null
      OR NOT a.Verkeersregelaar_voltageLampen IN ["42", "230"]
    )
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    voltageLampen: a.Verkeersregelaar_voltageLampen
  }
"""
        self.report = DQReport(name='report0083',
                               title='Verkeersregelaars hebben een voltage lampen die 42 of 230 is',
                               spreadsheet_id='1KQU0DrpB-LmU-DNOSzshYSA14aRmeomYcMF1xTm2Zek',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.voltageLampen IS NULL OR NOT a.voltageLampen IN ['42', '230']\nRETURN a.uuid, a.naam, a.voltageLampen"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
