from DQReport import DQReport


class Report0042:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0042',
                               title='EnergiemeterDNB en ForfaitaireAansluiting worden gevoed door een DNBLaagspanning',
                               spreadsheet_id='1QloH-HeEqyMpg2hnbAPSv8tLpxsLDOaXcPMywTj_Oi4',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (x {isActief: TRUE})
            WHERE (x:EnergiemeterDNB OR x:ForfaitaireAansluiting) AND NOT EXISTS((x)<-[:Voedt]-(:DNBLaagspanning {isActief: TRUE}))
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET energiemeterdnb_key      = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#EnergiemeterDNB" LIMIT 1 RETURN at._key)
LET forfaitaireaansluiting_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#ForfaitaireAansluiting" LIMIT 1 RETURN at._key)
LET dnlaagspanning_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#DNBLaagspanning" LIMIT 1 RETURN at._key)
LET voedt_key                = FIRST(FOR rt IN relatietypes FILTER rt.short == "Voedt" LIMIT 1 RETURN rt._key)

FOR x IN assets
  FILTER
    x.AIMDBStatus_isActief == true
    AND (x.assettype_key == energiemeterdnb_key OR x.assettype_key == forfaitaireaansluiting_key)

  LET dnb = FIRST(
    FOR v, rel IN INBOUND x assetrelaties
      FILTER
        rel.relatietype_key == voedt_key
        AND v.assettype_key == dnlaagspanning_key
        AND v.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN v
  )
  FILTER dnb == null

  RETURN {
    uuid: x._key,
    naam: x.AIMNaamObject_naam,
    typeURI: x.typeURI
  }
"""
