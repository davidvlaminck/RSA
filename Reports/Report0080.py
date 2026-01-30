from DQReport import DQReport


class Report0080:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND a.Verkeersregelaar_modelnaam == null
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0080',
                               title='Verkeersregelaars hebben een modelnaam',
                               spreadsheet_id='1JVX_XvZVgys7ntqWMDn32RolZPg_BvXpBIclMmQXxKI',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.modelnaam IS NULL\nRETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
