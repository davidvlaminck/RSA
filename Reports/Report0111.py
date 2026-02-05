from lib.reports.DQReport import DQReport


class Report0111:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.assettype_key == verkeersregelaar_key
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.Verkeersregelaar_vplanNummer != null

  // Cypher's `=~` is equivalent to AQL's REGEX_TEST.
  FILTER NOT REGEX_TEST(a.Verkeersregelaar_vplanNummer, "^[Vv]\\d{5,6}[vVwWsSxX]\\d{2}$")

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    vplanNummer: a.Verkeersregelaar_vplanNummer
  }
"""
        self.report = DQReport(name='report0111', title='Verkeersregelaars hebben een vplanNummer volgens bepaalde syntax',
                               spreadsheet_id='14g-EraRtSgEjC_f--Axt-6ZFWmgWvLhIXDvfw4DMBWQ', datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """
        // Verkeersregelaars hebben een vplannummer volgens bepaalde syntax
        MATCH (a:Verkeersregelaar {isActief:TRUE}) \n        WHERE NOT a.vplanNummer =~ '^[Vv]\\d{5,6}[vVwWsSxX]\\d{2}$'\n        RETURN a.uuid, a.naam, a.vplanNummer
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
