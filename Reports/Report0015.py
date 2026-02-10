from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0015(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET camera_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == "onderdeel#Camera"
    LIMIT 1
    RETURN at._key
)

FOR a IN assets
  FILTER
    a.assettype_key == camera_key
    AND a.AIMDBStatus_isActief == true

  COLLECT naam = a.AIMNaamObject_naam WITH COUNT INTO aantal
  FILTER aantal > 1

  FOR b IN assets
    FILTER
      b.assettype_key == camera_key
      AND b.AIMDBStatus_isActief == true
      AND b.AIMNaamObject_naam == naam

    RETURN {
      uuid: b._key,
      naam: b.AIMNaamObject_naam
    }
"""
        self.report = DQReport(name='report0015',
                               title='Camera\'s hebben een unieke naam',
                               spreadsheet_id='1GM6mBwfsLkEELjroSw-df6A2HXSQnOFAeudUzTybMQE',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Camera {isActief:TRUE})
        WITH a.naam AS naam, COUNT(a.naam) AS aantal
        WHERE aantal > 1
        MATCH (b:Camera {isActief:TRUE, naam:naam})
        RETURN b.uuid, b.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
