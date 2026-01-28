from DQReport import DQReport



class Report0085:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true
    AND a.AIMObject_theoretischeLevensduur == null
  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0085',
                               title='Verkeersregelaars hebben een ingevulde theoretische levensduur',
                               spreadsheet_id='11QZWCKGmGAkWWECLqtbuV4URFo3Gj4obrW4fMcEOT5s',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \nWHERE a.theoretischeLevensduur IS NULL\nRETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
