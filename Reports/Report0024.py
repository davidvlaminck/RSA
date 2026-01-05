from DQReport import DQReport


class Report0024:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0024',
                               title='Netwerkelementen hebben een unieke naam',
                               spreadsheet_id='1oV97_-ZrhMxHhsGkYv6vCfQLgivN8kH6BRsrveUP3yM',
                               datasource='Neo4J',
                               persistent_column='C')

        # query that fetches uuids of results
        self.report.result_query = """MATCH (a:Netwerkelement {isActief:TRUE})
        WITH a.naam AS naam, COUNT(a.naam) AS aantal
        WHERE aantal > 1
        MATCH (b:Netwerkelement {isActief:TRUE, naam:naam})
        RETURN b.uuid, b.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER
    n.assettype_key == netwerkelement_key
    AND n.AIMDBStatus_isActief == true

  COLLECT naam = n.AIMNaamObject_naam WITH COUNT INTO aantal
  FILTER aantal > 1

  FOR b IN assets
    FILTER
      b.assettype_key == netwerkelement_key
      AND b.AIMDBStatus_isActief == true
      AND b.AIMNaamObject_naam == naam
    RETURN {
      uuid: b._key,
      naam: b.AIMNaamObject_naam
    }
"""
