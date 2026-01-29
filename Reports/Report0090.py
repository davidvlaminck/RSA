from DQReport import DQReport


class Report0090:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Wegkantkast" LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR k IN assets
  FILTER k.assettype_key == wegkantkast_key
  FILTER k.AIMDBStatus_isActief == true
  FILTER k.Kast_indelingsplan == null

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
    indelingsplan: k.Kast_indelingsplan
  }
"""
        self.report = DQReport(name='report0090',
                               title='VRI Wegkantkasten hebben een indelingsplan',
                               spreadsheet_id='12-I-t8_kBb2TPfiFzDbdAOa0QwlscXvHBWjIos6ucbI',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE vr IS NOT NULL AND (k.`indelingsplan.bestandsnaam` IS NULL OR k.`indelingsplan.uri` IS NULL)\nRETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
