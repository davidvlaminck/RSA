from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0045(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET bitumineuzelaag_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#BitumineuzeLaag" LIMIT 1 RETURN at._key)
LET onderbouw_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Onderbouw" LIMIT 1 RETURN at._key)
LET ligtop_key          = FIRST(FOR rt IN relatietypes FILTER rt.short == "LigtOp" LIMIT 1 RETURN rt._key)

FOR b IN assets
  FILTER
    b.assettype_key            == bitumineuzelaag_key
    AND b.AIMDBStatus_isActief == true
  LET onderbouw = FIRST(
    FOR o, rel IN OUTBOUND b assetrelaties
      FILTER
        rel.relatietype_key == ligtop_key
        AND o.assettype_key == onderbouw_key
        AND o.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN o
  )
  FILTER onderbouw == null
  RETURN {
    uuid: b._key,
    toestand: b.toestand
  }
"""
        self.report = DQReport(name='report0045',
                               title='Een BitumineuzeLaag heeft steeds een ligtOp relatie naar een Onderbouw',
                               spreadsheet_id='1WRzZGpDXwtjg0CYa54pQBeYPfosNqe1-4g5c_xKWvrM',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """
            MATCH (b:BitumineuzeLaag {isActief: TRUE})
            WHERE NOT EXISTS((b)-[:LigtOp]->(:Onderbouw {isActief: TRUE}))
            RETURN b.uuid AS uuid, b.toestand AS toestand
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
