from lib.reports.DQReport import DQReport


class Report0088:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes   FILTER at.short_uri == "onderdeel#Wegkantkast"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes   FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes FILTER rt.short     == "Bevestiging"                LIMIT 1 RETURN rt._key)

FOR k IN assets
  FILTER
    k.assettype_key            == wegkantkast_key
    AND k.AIMDBStatus_isActief == true
    AND (
      k.Kast_afmeting.DtcAfmetingBxlxhInMm_breedte   == null
      OR k.Kast_afmeting.DtcAfmetingBxlxhInMm_lengte == null
      OR k.Kast_afmeting.DtcAfmetingBxlxhInMm_hoogte == null
      OR NOT (
        k.Kast_afmeting.DtcAfmetingBxlxhInMm_breedte < k.Kast_afmeting.DtcAfmetingBxlxhInMm_lengte
        AND k.Kast_afmeting.DtcAfmetingBxlxhInMm_breedte < k.Kast_afmeting.DtcAfmetingBxlxhInMm_hoogte
      )
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
    uuid:    k._key,
    naam:    k.AIMNaamObject_naam,
    lengte:  k.Kast_afmeting.DtcAfmetingBxlxhInMm_lengte,
    breedte: k.Kast_afmeting.DtcAfmetingBxlxhInMm_breedte,
    hoogte:  k.Kast_afmeting.DtcAfmetingBxlxhInMm_hoogte
  }
"""
        self.report = DQReport(name='report0088',
                               title='VRI Wegkantkasten hebben een afmeting',
                               spreadsheet_id='1WgLd7ESfGiJadbfALzJEwNG2-dNhUZALltPqk9WTynw',
                               datasource='ArangoDB',
                               persistent_column='F')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE vr IS NOT NULL AND (k.`afmeting.lengte` IS NULL OR k.`afmeting.breedte` IS NULL OR k.`afmeting.hoogte` IS NULL OR (CASE WHEN k.`afmeting.breedte` < k.`afmeting.lengte` AND k.`afmeting.breedte`< k.`afmeting.hoogte` THEN TRUE ELSE FALSE END) = FALSE)\nRETURN k.uuid, k.naam, k.`afmeting.lengte`, k.`afmeting.breedte`, k.`afmeting.hoogte`"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
