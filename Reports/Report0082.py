from DQReport import DQReport
from Reports.Report0087 import aql_query


class Report0082:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0082',
                               title='Verkeersregelaars hebben een programmeertool',
                               spreadsheet_id='11cw17fcyvJGy_QxYkou8rtChKKhoOYFqNfHoNi71XU8',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.programmeertool IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND a.Verkeersregelaar_programmeertool == null
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""