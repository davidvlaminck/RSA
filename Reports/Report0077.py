from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0077(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0077',
                               title='Verkeersregelaars hebben een ingevulde datum oprichting object',
                               spreadsheet_id='10K9cwkJIJQ2sXb71rvqm1MqtSj5k2M5FKtYUhE4mf2E',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.datumOprichtingObject IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)

aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key                == verkeersregelaar_key
    AND a.AIMDBStatus_isActief     == true
    AND a.Verkeersregelaar_datumOprichtingObject == null
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""