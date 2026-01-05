from DQReport import DQReport


class Report0019:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0019',
                               title='Paden zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1EsUciU3KV5EoDwv3NbAz-1SIPGXsRUrLQOTMZSstkZI',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (gl:Pad {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
        WITH gl, COUNT(p) AS aantal_poorten
        WHERE aantal_poorten = 2
        WITH collect(gl.uuid) AS good_paden
        MATCH (p:Pad {isActief:TRUE} )
        WHERE NOT p.uuid IN good_paden
        RETURN p.uuid, p.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET pad_key          = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#Pad" LIMIT 1 RETURN at._key)
LET netwerkpoort_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET hoortbij_key     = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

/// First: find uuids of Pads that have exactly 2 Netwerkpoorten
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

/// Then: all active Pads whose uuid/_key is not in good_paden
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