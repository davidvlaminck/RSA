from DQReport import DQReport


class Report0040:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0040',
                               title='DNBLaagspanning/DNBHoogspanning hebben een HoortBij relatie naar LS/HS respectievelijk',
                               spreadsheet_id='1WLXykE5pX9wiBqnSgJ1HTE8dtkjRydMxAnccLV3T1_U',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (dnbl:DNBLaagspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbl)-[:HoortBij]->(:LS {isActief: TRUE}))
            RETURN dnbl.uuid as uuid, dnbl.naam as naam, dnbl.typeURI as typeURI
            UNION
            MATCH (dnbh:DNBHoogspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbh)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN dnbh.uuid as uuid, dnbh.naam as naam, dnbh.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET dnlaagspanning_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#DNBLaagspanning" LIMIT 1 RETURN at._key)
LET dnbhoogspanning_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#DNBHoogspanning" LIMIT 1 RETURN at._key)
LET ls_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#LS" LIMIT 1 RETURN at._key)
LET hs_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#HS" LIMIT 1 RETURN at._key)
LET hoortbij_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

FOR a IN assets
  FILTER
    a.AIMDBStatus_isActief == true
    AND (
      (a.assettype_key == dnlaagspanning_key AND
        LENGTH(
          FOR l, rel IN OUTBOUND a assetrelaties
            FILTER
              rel.relatietype_key == hoortbij_key
              AND l.assettype_key == ls_key
              AND l.AIMDBStatus_isActief == true
            RETURN l
        ) == 0
      )
      OR
      (a.assettype_key == dnbhoogspanning_key AND
        LENGTH(
          FOR h, rel IN OUTBOUND a assetrelaties
            FILTER
              rel.relatietype_key == hoortbij_key
              AND h.assettype_key == hs_key
              AND h.AIMDBStatus_isActief == true
            RETURN h
        ) == 0
      )
    )

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    typeURI: a.typeURI
  }
"""
