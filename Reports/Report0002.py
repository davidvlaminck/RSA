from DQReport import DQReport


class Report0002:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0002',
                               title='TLCfipoorten hebben een sturingsrelatie naar een Verkeersregelaar',
                               spreadsheet_id='1C4OvyX6uQfe3eKa8A_ClsTfnmAcBy-45Q-18htdxHHM',
                               datasource='Neo4J',
                               persistent_column='C',
                               link_type='eminfra')

        self.report.result_query = """MATCH (a:Asset :TLCfiPoort {isActief:TRUE}) 
        WHERE NOT EXISTS ((a)-[:Sturing]-(:Verkeersregelaar {isActief:TRUE}))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET tlcfipoort_key      = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#TLCfiPoort" LIMIT 1 RETURN at._key)
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.assettype_key == tlcfipoort_key
  FILTER a.AIMDBStatus_isActief == true

  LET vr = FIRST(
    FOR v, rel IN ANY a sturing_relaties
      FILTER v.assettype_key == verkeersregelaar_key
      LIMIT 1
      RETURN v
  )
  FILTER vr == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""