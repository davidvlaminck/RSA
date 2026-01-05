from DQReport import DQReport


class Report0004:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0004',
                               title='Verkeersregelaars hebben een unieke naam',
                               spreadsheet_id='1aGZFPAeFgkQgU2XcrKhVKK1NPu-OEPuskPvWsnAyEYU',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WITH a.naam AS naam, COUNT(a.naam) AS aantal
        WHERE aantal > 1
        MATCH (b:Verkeersregelaar {isActief:TRUE, naam:naam})
        RETURN b.uuid, b.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET verkeersregelaar_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == "onderdeel#Verkeersregelaar"
    LIMIT 1
    RETURN at._key
)

FOR a IN assets
  FILTER
    a.assettype_key == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true

  COLLECT naam = a.AIMNaamObject_naam WITH COUNT INTO aantal
  FILTER aantal > 1

  FOR b IN assets
    FILTER
      b.assettype_key == verkeersregelaar_key
      AND b.AIMDBStatus_isActief == true
      AND b.AIMNaamObject_naam == naam

    RETURN {
      uuid: b._key,
      naam: b.AIMNaamObject_naam
    }
"""