from lib.reports.DQReport import DQReport


class Report0041:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET energiemeterdnb_key        = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#EnergiemeterDNB" LIMIT 1 RETURN at._key)
LET forfaitaireaansluiting_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#ForfaitaireAansluiting" LIMIT 1 RETURN at._key)
LET ls_key                     = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#LS" LIMIT 1 RETURN at._key)
LET hs_key                     = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#HS" LIMIT 1 RETURN at._key)
LET hoortbij_key               = FIRST(FOR rt IN relatietypes FILTER rt.short == "HoortBij" LIMIT 1 RETURN rt._key)

FOR x IN assets
  FILTER
    x.AIMDBStatus_isActief == true
    AND (x.assettype_key == energiemeterdnb_key OR x.assettype_key == forfaitaireaansluiting_key)

  LET ls = FIRST(
    FOR l, rel IN OUTBOUND x assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND l.assettype_key == ls_key
        AND l.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN l
  )
  LET hs = FIRST(
    FOR h, rel IN OUTBOUND x assetrelaties
      FILTER
        rel.relatietype_key == hoortbij_key
        AND h.assettype_key == hs_key
        AND h.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN h
  )
  FILTER ls == null AND hs == null

  RETURN {
    uuid: x._key,
    naam: x.AIMNaamObject_naam,
    typeURI: x.typeURI
  }
"""
        self.report = DQReport(name='report0041',
                               title='EnergiemeterDNB en ForfaitaireAansluiting hebben een HoortBij relatie naar een LS of HS',
                               spreadsheet_id='1_3NxUvqS6v_j9d7K4QzWBvN3ISveJ-poxW4_0XYEYFM',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (x {isActief: TRUE})\n            WHERE (x:EnergiemeterDNB OR x:ForfaitaireAansluiting) AND NOT EXISTS((x)-[:HoortBij]->(:LS {isActief: TRUE})) AND NOT EXISTS((x)-[:HoortBij]->(:HS {isActief: TRUE}))\n            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
