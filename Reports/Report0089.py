from DQReport import DQReport


class Report0089:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0089',
                               title='VRI Wegkantkasten hebben een elektrisch schema',
                               spreadsheet_id='1kt7UYbiXzf222WnZB-dTTYzp3cIMjAA9WFi0Z2BvvCU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.`elektrischSchema.bestandsnaam` IS NULL OR k.`elektrischSchema.uri` IS NULL)
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes   FILTER at.short_uri == "onderdeel#Wegkantkast"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes   FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes FILTER rt.short     == "Bevestiging"                LIMIT 1 RETURN rt._key)

FOR k IN assets
  FILTER
    k.assettype_key            == wegkantkast_key
    AND k.AIMDBStatus_isActief == true
    AND (
      k.Wegkantkast_elektrischSchema.DtcDocument_bestandsnaam == null OR
      k.Wegkantkast_elektrischSchema.DtcDocument_uri          == null
    )

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
    elektrischSchema_bestandsnaam: k.Wegkantkast_elektrischSchema.DtcDocument_bestandsnaam,
    elektrischSchema_uri: k.Wegkantkast_elektrischSchema.DtcDocument_uri
  }
"""