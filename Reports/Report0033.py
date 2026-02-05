from lib.reports.DQReport import DQReport


class Report0033:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET vlan_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#VLAN" LIMIT 1 RETURN at._key)
LET l2accessstructuur_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#L2AccessStructuur" LIMIT 1 RETURN at._key)
LET hoortbij_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

FOR n IN assets
  FILTER
    n.assettype_key == vlan_key
    AND n.AIMDBStatus_isActief == true

  LET l2access = FIRST(
    FOR l2, rel IN OUTBOUND n assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND l2.assettype_key == l2accessstructuur_key
        AND l2.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN l2
  )
  FILTER l2access == null

  RETURN {
    uuid: n._key,
    naam: n.AIMNaamObject_naam
  }  
"""
        self.report = DQReport(name='report0033',
                               title="VLAN objecten hebben een HoortBij relatie met een L2AccesStructuur",
                               spreadsheet_id='12urCVlUXm_KbNCrQS1MH5kVqNKak3n5DdQlAnk8mn9w',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (n:VLAN {isActief:TRUE}) \n        WHERE NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))\n        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
