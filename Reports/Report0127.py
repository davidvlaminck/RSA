from DQReport import DQReport


class Report0127:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET kabelnetbuis_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#KabelnetBuis" LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.assettype_key == kabelnetbuis_key
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
        self.report = DQReport(name='report0127',
                               title='KabelnetBuis heeft een relatie met een andere asset',
                               spreadsheet_id='1miMzTSeLtpLlK61lijv1Fzh88xC4U9RKVmwZnMjmdPU',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """
        // KabelnetBuis zonder relatie
        MATCH (n:KabelnetBuis {isActief:true})
        WHERE NOT (n)--()
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
