from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0018(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET link_key          = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#Link" LIMIT 1 RETURN at._key)
LET netwerkpoort_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET hoortbij_key      = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

LET good_links = (
  FOR gl IN assets
    FILTER
      gl.assettype_key == link_key
      AND gl.AIMDBStatus_isActief == true

    LET aantal_poorten = LENGTH(
      FOR p, rel IN INBOUND gl assetrelaties
        FILTER
          rel.relatietype_key == hoortbij_key
          AND p.assettype_key == netwerkpoort_key
          AND p.AIMDBStatus_isActief == true
        RETURN 1
    )
    FILTER aantal_poorten == 2
    RETURN gl._key
)

FOR l IN assets
  FILTER
    l.assettype_key == link_key
    AND l.AIMDBStatus_isActief == true
    AND l._key NOT IN good_links

  RETURN {
    uuid: l._key,
    naam: l.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0018',
                               title='Linken zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1U_27rorzzxcoBOxLoHIN8Vt20idDafrb5DGE_ECWVAw',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (gl:Link {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})\n        WITH gl, COUNT(p) AS aantal_poorten\n        WHERE aantal_poorten = 2\n        WITH collect(gl.uuid) AS good_links\n        MATCH (l:Link {isActief:TRUE} )\n        WHERE NOT l.uuid IN good_links\n        RETURN l.uuid, l.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
