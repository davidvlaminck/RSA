from DQReport import DQReport


class Report0005:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0005',
                               title='Verkeersregelaars en TLCfiPoorten hebben een HoortBij relatie naar VRLegacy objecten',
                               spreadsheet_id='1daDivHkKfMRamwgpty9swGF4Kz68MBjJlSE5SR2GqFQ',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (a:onderdeel {isActief:TRUE}) 
        WHERE (a:Verkeersregelaar OR a:TLCfiPoort) AND NOT EXISTS ((a)-[:HoortBij]->(:VRLegacy {isActief:TRUE}))
        RETURN a.uuid, a.naam, a.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET verkeersregelaar_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == "onderdeel#Verkeersregelaar"
    LIMIT 1
    RETURN at._key
)
LET tlcfipoort_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == "onderdeel#TLCfiPoort"
    LIMIT 1
    RETURN at._key
)
LET vrlegacy_key = FIRST(
  FOR at IN assettypes
    FILTER at.short_uri == "lgc:installatie#VRLegacy"
    LIMIT 1
    RETURN at._key
)
LET hoortbij_key = FIRST(
  FOR rt IN relatietypes
    FILTER rt.short == "HoortBij"
    LIMIT 1
    RETURN rt._key
)

FOR a IN assets
  FILTER
    a.AIMDBStatus_isActief == true
    AND (a.assettype_key == verkeersregelaar_key OR a.assettype_key == tlcfipoort_key)

  LET vrlegacy = FIRST(
    FOR v, rel IN OUTBOUND a assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND v.assettype_key == vrlegacy_key
        AND v.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN v
  )
  FILTER vrlegacy == null

  RETURN {
    uuid:   a._key,
    naam:   a.AIMNaamObject_naam,
    typeURI: a.typeURI
  }
"""