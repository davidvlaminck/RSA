from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0042(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET energiemeterdnb_key         = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#EnergiemeterDNB\" LIMIT 1 RETURN at._key)
LET forfaitaireaansluiting_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#ForfaitaireAansluiting\" LIMIT 1 RETURN at._key)
LET dnlaagspanning_key          = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#DNBLaagspanning\" LIMIT 1 RETURN at._key)

FOR x IN assets
  FILTER x.AIMDBStatus_isActief == true
  FILTER (x.assettype_key == energiemeterdnb_key OR x.assettype_key == forfaitaireaansluiting_key)

  LET dnb = FIRST(
    FOR v, rel IN INBOUND x voedt_relaties
      FILTER v.assettype_key == dnlaagspanning_key
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
        self.report = DQReport(name='report0042',
                               title='EnergiemeterDNB en ForfaitaireAansluiting worden gevoed door een DNBLaagspanning',
                               spreadsheet_id='1QloH-HeEqyMpg2hnbAPSv8tLpxsLDOaXcPMywTj_Oi4',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (x {isActief: TRUE})\n            WHERE (x:EnergiemeterDNB OR x:ForfaitaireAansluiting) AND NOT EXISTS((x)<-[:Voedt]-(:DNBLaagspanning {isActief: TRUE}))\n            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
