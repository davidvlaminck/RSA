from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0026(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET pad_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Pad" LIMIT 1 RETURN at._key)
LET zpad_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Zpad" LIMIT 1 RETURN at._key)
LET hoortbij_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

FOR a IN assets
  FILTER
    a.assettype_key == pad_key
    AND a.AIMDBStatus_isActief == true

  LET zpad = FIRST(
    FOR z, rel IN OUTBOUND a assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND z.assettype_key == zpad_key
        AND z.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN z
  )
  FILTER zpad == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0026',
                               title='Paden hebben een HoortBij relatie naar Zpad objecten',
                               spreadsheet_id='18KfmYhpxc75ECyN54WFtKrG4Hdz6GPCXzH5i8Zi0144',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Asset:Pad {isActief:TRUE}) \n        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Asset:Zpad {isActief:TRUE}))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
