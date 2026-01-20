from DQReport import DQReport


class Report0125:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0125',
                               title='KabelnetToegang heeft een relatie met een andere asset',
                               spreadsheet_id='1FVilNqQXxNI0HB9Zu2Dc4e9McODPw-eDPeG0h3i0_x4',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetToegang zonder relatie
        MATCH (n:KabelnetToegang {isActief:True})
        WHERE NOT (n)--()
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


# AQL equivalent (documentation / future migration)
# Cypher:
# MATCH (n:KabelnetToegang {isActief:True})
# WHERE NOT (n)--()
# RETURN n.uuid, n.toestand, n.isActief

aql_query = """
LET kabelnettoegang_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#KabelnetToegang" LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.assettype_key == kabelnettoegang_key

  // (n)--()  => at least one edge exists in either direction
  LET has_any_relation = LENGTH(
    FOR v, e IN ANY n assetrelaties
      FILTER e.AIMDBStatus_isActief == true
      FILTER v.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_any_relation

  RETURN {
    uuid: n._key,
    toestand: n.toestand,
    isActief: n.AIMDBStatus_isActief
  }
"""

