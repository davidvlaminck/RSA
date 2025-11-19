from DQReport import DQReport


class Report0092:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0092',
                               title='VRI Wegkantkasten hebben een ingevulde verlichting',
                               spreadsheet_id='1NMv8jIX0x-WBOrks5fIyAL6FNjlwbKqOVJpFQBCfjrk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND k.heeftVerlichting IS NULL
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Wegkantkast"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes   FILTER rt.short     == "Bevestiging"                LIMIT 1 RETURN rt._key)

FOR k IN assets
  FILTER
    k.assettype_key             == wegkantkast_key
    AND k.AIMDBStatus_isActief  == true
    AND k.Kast_heeftVerlichting == null

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
    heeftVerlichting: k.Kast_heeftVerlichting
  }
"""