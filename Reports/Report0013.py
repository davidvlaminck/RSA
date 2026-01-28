from DQReport import DQReport


class Report0013:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET stroomkring_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Stroomkring\"       LIMIT 1 RETURN at._key)
LET laagspanningsbord_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Laagspanningsbord\" LIMIT 1 RETURN at._key)
LET bevestiging_key       = FIRST(FOR rt IN relatietypes FILTER rt.short == \"Bevestiging\"                   LIMIT 1 RETURN rt._key)

FOR s IN assets
  FILTER
    s.assettype_key == stroomkring_key
    AND s.AIMDBStatus_isActief == true

  LET lsb = FIRST(
    FOR other, rel IN ANY s assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND other.assettype_key == laagspanningsbord_key
        AND other.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN other
  )
  FILTER lsb == null

  RETURN {
    uuid: s._key,
    naam: s.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0013',
                               title='Stroomkringen hebben een Bevestiging relatie met een Laagspanningsbord',
                               spreadsheet_id='1az4rh44wIf0KkILgQqV0iJeb47SbRW-dgq_DP3GDDeo',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (s:Stroomkring {isActief:TRUE}) \n        WHERE NOT EXISTS ((s)-[:Bevestiging]-(:Laagspanningsbord {isActief:TRUE}))\n        RETURN s.uuid, s.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
