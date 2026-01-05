from DQReport import DQReport


class Report0017:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0017',
                               title='Netwerkkaarten hebben een Bevestiging relatie met een Netwerkelement',
                               spreadsheet_id='1UfYhxcM0z8uq9-GwfDJhHNVpuhoWtUprrPGMfPSXeGk',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkkaart {isActief:TRUE})
        WHERE NOT EXISTS ((n)-[:Bevestiging]-(:Netwerkelement {isActief:TRUE}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET netwerkkaart_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkkaart"    LIMIT 1 RETURN at._key)
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement"  LIMIT 1 RETURN at._key)
LET bevestiging_key    = FIRST(FOR rt IN relatietypes FILTER rt.short == "Bevestiging"                 LIMIT 1 RETURN rt._key)

FOR n IN assets
  FILTER
    n.assettype_key == netwerkkaart_key
    AND n.AIMDBStatus_isActief == true

  LET ne = FIRST(
    FOR e, rel IN ANY n assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND e.assettype_key == netwerkelement_key
        AND e.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN e
  )
  FILTER ne == null

  RETURN {
    uuid: n._key,
    naam: n.AIMNaamObject_naam
  }
"""