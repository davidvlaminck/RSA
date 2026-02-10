from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0093(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Wegkantkast" LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR k IN assets
  FILTER k.assettype_key == wegkantkast_key
  FILTER k.AIMDBStatus_isActief == true
  FILTER k.Buitenkast_ipKlasse == null

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
    ipKlasse: k.Buitenkast_ipKlasse
  }
"""
        self.report = DQReport(name='report0093',
                               title='VRI Wegkantkasten hebben een ingress protection klasse',
                               spreadsheet_id='1avx8BOU2bvwYBmE0_ntKVcz6Uy3-o72mNXgHZMWeaSU',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE vr IS NOT NULL AND k.ipKlasse IS NULL\nRETURN k.uuid, k.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
