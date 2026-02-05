from lib.reports.DQReport import DQReport


class Report0087:
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
    AND k.Wegkantkast_datumOprichtingObject == null

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
  }
"""
        self.report = DQReport(name='report0087',
                               title='VRI Wegkantkasten hebben een ingevulde datum oprichting object',
                               spreadsheet_id='13Y1AmHPji5z-Zy-uDF6-YstSF0DKDx2oKUHCs7iU6mU',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE k.datumOprichtingObject IS NULL AND vr IS NOT NULL\nRETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
