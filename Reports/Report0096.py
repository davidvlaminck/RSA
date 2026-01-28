from DQReport import DQReport


class Report0096:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Wegkantkast" LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR k IN assets
  FILTER k.assettype_key == wegkantkast_key
  FILTER k.AIMDBStatus_isActief == true
  FILTER k.Wegkantkast_type == null

  LET vr = FIRST(
    FOR v, rel IN ANY k bevestiging_relaties
      FILTER v.assettype_key == verkeersregelaar_key
      LIMIT 1
      RETURN v
  )
  FILTER vr != null

  RETURN {
    uuid: k._key,
    naam: k.AIMNaamObject_naam,
    type: k.Wegkantkast_type
  }
"""
        self.report = DQReport(name='report0096',
                               title='VRI Wegkantkasten hebben een type',
                               spreadsheet_id='1QprGpAuoCALC981B02kgAQJhj3CV1B6KYXPTF1pgacU',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE vr IS NOT NULL AND k.type IS NULL\nRETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
