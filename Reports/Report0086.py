from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0086(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Verkeersregelaar\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND (
      a.toestand == null
      OR a.toestand == \"in-ontwerp\"
    )
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    toestand: a.toestand
  }
"""
        self.report = DQReport(name='report0086',
                               title='Verkeersregelaars hebben een ingevulde toestand',
                               spreadsheet_id='1EJjhp70-7bbrHaTbqPuZdn86rrXw30TEUYns7Kvi1dQ',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.toestand IS NULL OR a.toestand = 'in-ontwerp'\nRETURN a.uuid, a.naam, a.toestand"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
