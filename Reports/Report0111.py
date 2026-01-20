from DQReport import DQReport


class Report0111:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0111', title='Verkeersregelaars hebben een vplanNummer volgens bepaalde syntax',
                               spreadsheet_id='14g-EraRtSgEjC_f--Axt-6ZFWmgWvLhIXDvfw4DMBWQ', datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """
        // Verkeersregelaars hebben een vplannummer volgens bepaalde syntax
        MATCH (a:Verkeersregelaar {isActief:TRUE}) 
        WHERE NOT a.vplanNummer =~ '^[Vv]\d{5,6}[vVwWsSxX]\d{2}$'
        RETURN a.uuid, a.naam, a.vplanNummer
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# AQL equivalent (documentation / future migration)
# Cypher:
# MATCH (a:Verkeersregelaar {isActief:TRUE})
# WHERE NOT a.vplanNummer =~ '^[Vv]\d{5,6}[vVwWsSxX]\d{2}$'
# RETURN a.uuid, a.naam, a.vplanNummer
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
