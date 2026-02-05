from lib.reports.DQReport import DQReport


class Report0014:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET stroomkring_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Stroomkring" LIMIT 1 RETURN at._key)
LET laagspanningsbord_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Laagspanningsbord" LIMIT 1 RETURN at._key)
LET lsdeel_key            = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#LSDeel" LIMIT 1 RETURN at._key)

FOR s IN assets
  FILTER s.AIMDBStatus_isActief == true
  FILTER (s.assettype_key == stroomkring_key OR s.assettype_key == laagspanningsbord_key)

  LET lsdeel = FIRST(
    FOR l, rel IN OUTBOUND s hoortbij_relaties
      FILTER l.assettype_key == lsdeel_key
      LIMIT 1
      RETURN l
  )
  FILTER lsdeel == null

  RETURN {
    uuid: s._key,
    naam: s.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0014',
                               title='Stroomkringen en Laagspanningsborden hebben een HoortBij relatie met een LSDeel object',
                               spreadsheet_id='1iVs6wP1WcdHxEUsx5N_NlunvGU4LycRUO1_4j03Nwzo',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (s:onderdeel {isActief:TRUE}) 
        WHERE (s:Stroomkring OR s:Laagspanningsbord) AND NOT EXISTS ((s)-[:HoortBij]->(:LSDeel {isActief:TRUE}))
        RETURN s.uuid, s.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
