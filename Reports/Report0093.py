from DQReport import DQReport


class Report0093:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0093',
                               title='VRI Wegkantkasten hebben een ingress protection klasse',
                               spreadsheet_id='1avx8BOU2bvwYBmE0_ntKVcz6Uy3-o72mNXgHZMWeaSU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.ipKlasse IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Wegkantkast"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes   FILTER rt.short     == "Bevestiging"                LIMIT 1 RETURN rt._key)

FOR k IN assets
  FILTER
    k.assettype_key            == wegkantkast_key
    AND k.AIMDBStatus_isActief == true
    AND k.Buitenkast_ipKlasse  == null

  LET vr = FIRST(
    FOR v, rel IN ANY k assetrelaties
      FILTER
        rel.relatietype_key          == bevestiging_key
        AND rel.AIMDBStatus_isActief == true
        AND v.assettype_key          == verkeersregelaar_key
        AND v.AIMDBStatus_isActief   == true
      LIMIT 1
      RETURN v
  )
  FILTER vr != null

  RETURN {
    uuid: k._key,
    naam: k.AIMNaamObject_naam,
    ipKlasse: k.Buitenkast_ipKlasse
  }
"""