from DQReport import DQReport


class Report0099:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0099',
                               title='VRI Wegkantkasten hebben een conforme naam',
                               spreadsheet_id='1tTJMTTWFLY9VV0imGZPRSCrC4qEULV9tWviO8JBQIfA',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.naam is NULL OR NOT (k.naam =~ '^\d{3}[ACG]\dX01$' OR k.naam =~ '^W[WO]\d{4}X01$'))
RETURN k.uuid, k.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET wegkantkast_key      = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Wegkantkast"      LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes     FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET bevestiging_key      = FIRST(FOR rt IN relatietypes   FILTER rt.short     == "Bevestiging"                LIMIT 1 RETURN rt._key)

FOR v IN assets
  FILTER
    v.assettype_key            == verkeersregelaar_key
    AND v.AIMDBStatus_isActief == true

  FOR k, rel IN ANY v assetrelaties
    FILTER
      rel.relatietype_key          == bevestiging_key
      AND rel.AIMDBStatus_isActief == true
      AND k.assettype_key          == wegkantkast_key
      AND k.AIMDBStatus_isActief   == true
      AND (
        k.AIMNaamObject_naam == NULL
        OR NOT (
          REGEX_TEST(k.AIMNaamObject_naam, "^\\d{3}[ACG]\\dX01$")
          OR REGEX_TEST(k.AIMNaamObject_naam, "^W[WO]\\d{4}X01$")
        )
      )

  COLLECT uuid = k._key, naam = k.AIMNaamObject_naam
  RETURN { uuid, naam }
"""

