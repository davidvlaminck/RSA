from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0098(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes     FILTER at.short_uri == \"onderdeel#Wegkantkast\"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes     FILTER at.short_uri == \"onderdeel#Verkeersregelaar\" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes   FILTER rt.short     == \"Bevestiging\"                LIMIT 1 RETURN rt._key)

FOR k IN assets
  FILTER
    k.assettype_key                        == wegkantkast_key
    AND k.AIMDBStatus_isActief             == true
    AND k.AIMObject_theoretischeLevensduur == null

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
    naam: k.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0098',
                               title='VRI Wegkantkasten hebben een theoretische levensduur',
                               spreadsheet_id='1guhz-Sb-eBSFWEpf2Ayn1VboyTJG98lINM3_ppEROfA',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) \nWHERE vr IS NOT NULL AND k.theoretischeLevensduur IS NULL\nRETURN k.uuid, k.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
