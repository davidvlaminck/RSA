from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0019(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET pad_key          = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#Pad" LIMIT 1 RETURN at._key)
LET netwerkpoort_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET hoortbij_key     = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

LET good_paden = (
  FOR gl IN assets
    FILTER
      gl.assettype_key == pad_key
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

FOR p IN assets
  FILTER
    p.assettype_key == pad_key
    AND p.AIMDBStatus_isActief == true
    AND p._key NOT IN good_paden

  RETURN {
    uuid: p._key,
    naam: p.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0019',
                               title='Paden zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1EsUciU3KV5EoDwv3NbAz-1SIPGXsRUrLQOTMZSstkZI',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (gl:Pad {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})\n        WITH gl, COUNT(p) AS aantal_poorten\n        WHERE aantal_poorten = 2\n        WITH collect(gl.uuid) AS good_paden\n        MATCH (p:Pad {isActief:TRUE} )\n        WHERE NOT p.uuid IN good_paden\n        RETURN p.uuid, p.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
