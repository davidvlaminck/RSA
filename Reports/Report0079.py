from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0079(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND a.Verkeersregelaar_merk == null
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0079',
                               title='Verkeersregelaars hebben een merk',
                               spreadsheet_id='1xdMtHKwBHN23eNMjAKyAVvyl2oAQuzauefuOx6jEQNk',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.merk IS NULL\nRETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
