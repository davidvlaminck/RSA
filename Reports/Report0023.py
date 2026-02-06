from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0023(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET camera_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Camera" LIMIT 1 RETURN at._key)

FOR c IN assets
  FILTER
    c.assettype_key == camera_key
    AND c.AIMDBStatus_isActief == true

  LET toezichter = FIRST(
    FOR v, e IN 1..1 OUTBOUND c._id betrokkenerelaties
      FILTER e.rol == "toezichter"
      RETURN v
  )

  FILTER toezichter == null

  RETURN {
    uuid: c._key,
    naam: c.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0023',
                               title='Camera\'s hebben een toezichter',
                               spreadsheet_id='1jkBCSgtZ8jlwA-Ah62I17pVtybrqPZSreXgrC6kWKoQ',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (c:Camera {isActief:TRUE})
        WHERE NOT EXISTS ((c)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))
        RETURN c.uuid, c.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
