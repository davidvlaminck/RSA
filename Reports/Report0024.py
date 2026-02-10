from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0024(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)
LET netwerkkaart_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkkaart" LIMIT 1 RETURN at._key)
LET bevestiging_key    = FIRST(FOR rt IN relatietypes FILTER rt.short == "Bevestiging" LIMIT 1 RETURN rt._key)

FOR n IN assets
  FILTER n.assettype_key == netwerkelement_key
  FILTER n.AIMDBStatus_isActief == true

  LET kaart = FIRST(
    FOR k, rel IN ANY n assetrelaties
      FILTER rel.relatietype_key == bevestiging_key
      FILTER k.assettype_key == netwerkkaart_key
      LIMIT 1
      RETURN k
  )
  FILTER kaart == null

  RETURN {
    uuid: n._key,
    naam: n.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0024',
                               title='Netwerkelementen hebben een Bevestiging relatie met een Netwerkkaart',
                               spreadsheet_id='1oV97_-ZrhMxHhsGkYv6vCfQLgivN8kH6BRsrveUP3yM',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (n:Netwerkelement {isActief:TRUE}) \n        WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkkaart {isActief:TRUE}))\n        RETURN n.uuid, n.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
