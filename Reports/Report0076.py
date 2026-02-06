from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0076(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0076',
                               title='Verkeersregelaars hebben een installatieverantwoordelijke',
                               spreadsheet_id='1JGhVFeXXejMHRupSqqKgSEaz384vf4NNrJ8OyDs4NeM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WHERE NOT EXISTS ((a)-[:HeeftBetrokkene {rol:'installatieverantwoordelijke'}]->(:Agent))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)

aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.assettype_key == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true

  LET betrokkene = FIRST(
    FOR v, e IN 1..1 OUTBOUND a._id betrokkenerelaties
      FILTER e.rol == "installatieverantwoordelijke"
      RETURN v
  )

  FILTER betrokkene == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""