from DQReport import DQReport


class Report0018:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0018',
                               title='Linken zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1U_27rorzzxcoBOxLoHIN8Vt20idDafrb5DGE_ECWVAw',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (gl:Link {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
        WITH gl, COUNT(p) AS aantal_poorten
        WHERE aantal_poorten = 2
        WITH collect(gl.uuid) AS good_links
        MATCH (l:Link {isActief:TRUE} )
        WHERE NOT l.uuid IN good_links
        RETURN l.uuid, l.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET link_key          = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#Link" LIMIT 1 RETURN at._key)
LET netwerkpoort_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET hoortbij_key      = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

/// First: find uuids of Links that have exactly 2 Netwerkpoorten
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

/// Then: all active Links whose uuid/_key is not in good_links
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