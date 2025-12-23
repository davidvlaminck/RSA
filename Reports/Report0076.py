from DQReport import DQReport


class Report0076:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0076',
                               title='Verkeersregelaars hebben een installatieverantwoordelijke',
                               spreadsheet_id='1JGhVFeXXejMHRupSqqKgSEaz384vf4NNrJ8OyDs4NeM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WHERE NOT EXISTS ((a)-[:HeeftBetrokkene {rol:'installatieverantwoordelijke'}]->(:Agent))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET agent_key            = FIRST(FOR at IN assettypes FILTER at.short_uri == "betrokkene#Agent" LIMIT 1 RETURN at._key)
LET heeftbetrokkene_key  = FIRST(FOR rt IN relatietypes FILTER rt.short == "HeeftBetrokkene" LIMIT 1 RETURN rt._key)

FOR a IN assets
  FILTER
    a.assettype_key            == verkeersregelaar_key
    AND a.AIMDBStatus_isActief == true

  LET betrokkene = FIRST(
    FOR b, rel IN OUTBOUND a assetrelaties
      FILTER
        rel.relatietype_key == heeftbetrokkene_key
        AND rel.rol == "installatieverantwoordelijke"
        AND b.assettype_key == agent_key
      LIMIT 1
      RETURN b
  )
  FILTER betrokkene == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""