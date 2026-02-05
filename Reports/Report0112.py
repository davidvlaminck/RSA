from lib.reports.DQReport import DQReport


class Report0112:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Verkeersregelaar\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.assettype_key == verkeersregelaar_key
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.Verkeersregelaar_vplanDatum == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    vplanNummer: a.Verkeersregelaar_vplanNummer,
    vplanDatum: a.Verkeersregelaar_vplanDatum
  }
"""
        self.report = DQReport(name='report0112', title='Verkeersregelaars hebben een vplanDatum',
                               spreadsheet_id='1701KVEMJAco3NPxfgOtHP0byI9_MQ1yhb1EQ3ujvU9I', datasource='ArangoDB',
                               persistent_column='E')

        self.report.result_query = aql_query
        self.report.cypher_query = """
        MATCH (a:Verkeersregelaar {isActief:TRUE}) 
        WHERE a.vplanDatum is null
        RETURN a.uuid, a.naam, a.vplanNummer, a.vplanDatum
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
