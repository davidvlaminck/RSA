from DQReport import DQReport


class Report0037:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER n.assettype_key == netwerkelement_key
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.toestand == "in-gebruik"
  FILTER n.Netwerkelement_gebruik == "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkelemGebruik/l2-switch"

  LET voedt_from = FIRST(
    FOR v, rel IN INBOUND n voedt_relaties
      LIMIT 1
      RETURN v
  )

  FILTER voedt_from == null

  RETURN {
    uuid: n._key,
    naampad: n.NaampadObject_naampad,
    gebruik: n.Netwerkelement_gebruik
  }
"""
        self.report = DQReport(name='report0037',
                               title="L2 switches worden gevoed",
                               spreadsheet_id='1mPx2y3XvOGNCRoYPLTHv6Xb5kn4bQCt3Aii0zT7ZdUc',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (n:Netwerkelement {isActief:TRUE, toestand:'in-gebruik', gebruik:'l2-switch'})\n        WHERE NOT EXISTS ((n)-[:HoortBij]-(:Asset {isActief:TRUE})<-[:Voedt]-(:Asset {isActief:TRUE}))\n        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
