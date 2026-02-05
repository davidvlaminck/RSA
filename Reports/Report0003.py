from lib.reports.DQReport import DQReport


class Report0003:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == \"onderdeel#Verkeersregelaar\"
    LIMIT 1
    RETURN at._key
)
LET wegkantkast_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == \"onderdeel#Wegkantkast\"
    LIMIT 1
    RETURN at._key
)
LET bevestiging_key = FIRST(
  FOR rt IN relatietypes
    FILTER rt.short == \"Bevestiging\"
    LIMIT 1
    RETURN rt._key
)

FOR a IN assets
  FILTER
    a.assettype_key == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true

  LET kast = FIRST(
    FOR k, rel IN ANY a assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND k.assettype_key == wegkantkast_key
        AND k.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN k
  )
  FILTER kast == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0003',
                               title='Verkeersregelaars hebben een Bevestiging relatie naar een Wegkantkast',
                               spreadsheet_id='1tud5st23sWAKYxdtGUmNHS1Tt54GW31HwkJPaXYXrtE',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \n        WHERE NOT EXISTS ((a)-[:Bevestiging]-(:Wegkantkast {isActief:TRUE}))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
