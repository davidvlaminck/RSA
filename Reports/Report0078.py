from lib.reports.DQReport import DQReport


class Report0078:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key                == verkeersregelaar_key
    AND a.AIMDBStatus_isActief     == true
    AND (
      a.Verkeersregelaar_coordinatiewijze == null
      OR LENGTH(a.Verkeersregelaar_coordinatiewijze) == 0
      OR a.Verkeersregelaar_coordinatiewijze[0] == null
    )
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0078',
                               title='Verkeersregelaars hebben een coördinatiewijze',
                               spreadsheet_id='1uhl_HnxT5H9XrEjswHlkR_jvl4nx99ss9UOM-3Yjy_M',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.`coordinatiewijze[0]` IS NULL\nRETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
