from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0020(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET zpad_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "installatie#Zpad" LIMIT 1 RETURN at._key)
LET netwerkpoort_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET hoortbij_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

FOR z IN assets
  FILTER
    z.assettype_key == zpad_key
    AND z.AIMDBStatus_isActief == true
    AND z.toestand == "in-gebruik"

  LET n_netwerkpoort = LENGTH(
    FOR n, rel IN INBOUND z assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND n.assettype_key == netwerkpoort_key
        AND n.AIMDBStatus_isActief == true
      RETURN n
  )
  FILTER n_netwerkpoort != 2

  RETURN {
    uuid: z._key,
    naam: z.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0020',
                               title='Zpaden zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                               spreadsheet_id='1dudUqdNZTf1lPcAFbv_kSTI0gIBvAkX0TUumvwR-O7M',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (z:Zpad {isActief:TRUE})\n        WHERE z.toestand = \"in-gebruik\"\n        OPTIONAL MATCH (z)<-[:HoortBij]-(n:Netwerkpoort {isActief:TRUE})\n        WITH z, count(n) AS n_netwerkpoort\n        WHERE n_netwerkpoort <> 2\n        RETURN z.uuid, z.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
