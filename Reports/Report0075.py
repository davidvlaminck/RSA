from DQReport import DQReport


class Report0075:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true

  LET toezichter = FIRST(
    FOR v, e IN 1..1 OUTBOUND a._id betrokkenerelaties
      FILTER e.rol == "toezichter"
      RETURN v
  )

  FILTER toezichter == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0075',
                               title='Verkeersregelaars hebben een toezichter',
                               spreadsheet_id='1n2_75LTrJ9UazN6qQaDSZ6LT2q8IDjxJLaRmqUnikbs',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})\n        WHERE NOT EXISTS ((a)-[:HeeftBetrokkene {rol:'toezichter'}]->(:Agent))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
