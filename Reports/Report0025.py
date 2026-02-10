from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0025(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET link_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"installatie#Link\" LIMIT 1 RETURN at._key)
LET pad_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"installatie#Pad\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.assettype_key == link_key
  FILTER a.AIMDBStatus_isActief == true

  LET pad = FIRST(
    FOR p IN OUTBOUND a hoortbij_relaties
      FILTER p.assettype_key == pad_key
      LIMIT 1
      RETURN p
  )
  FILTER pad == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0025',
                               title='Linken hebben een HoortBij relatie naar Pad objecten',
                               spreadsheet_id='1PwWn1E4VRsXRa8L7Lh0Pmjy1Z0ZKCoclDO0bvHx3EaY',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Asset :Link {isActief:TRUE}) \n        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Pad {isActief:TRUE}))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
