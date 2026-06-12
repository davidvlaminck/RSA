from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0230(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET mivmodule_key = "7f59b64e"
LET wegkantkast_key = "c3601915"

FOR miv IN assets
  FILTER miv.AIMDBStatus_isActief == true
  FILTER miv.assettype_key == mivmodule_key
  LET kasten = (
    FOR rel IN assetrelaties
      FILTER rel.relatietype_key == "3ff9"
      FILTER rel._from == CONCAT('assets/', miv._key)
      LET wk = DOCUMENT(rel._to)
      FILTER wk != null
      FILTER wk.AIMDBStatus_isActief == true
      FILTER wk.assettype_key == wegkantkast_key
      RETURN {
        uuid: wk._key,
        naam: wk.AIMNaamObject_naam,
        naampad: wk.NaampadObject_naampad
      }
  )
  FILTER LENGTH(kasten) > 1
  LET kast1 = kasten[0]
  LET kast2 = kasten[1]
  LET kast3 = kasten[2]
  SORT miv.AIMNaamObject_naam ASC
  RETURN {
    miv_uuid: miv._key,
    miv_naam: miv.AIMNaamObject_naam,
    miv_naampad: miv.NaampadObject_naampad,
    aantal_kasten: LENGTH(kasten),
    kast1_uuid: kast1 ? kast1.uuid : null,
    kast1_naam: kast1 ? kast1.naam : null,
    kast1_naampad: kast1 ? kast1.naampad : null,
    kast2_uuid: kast2 ? kast2.uuid : null,
    kast2_naam: kast2 ? kast2.naam : null,
    kast2_naampad: kast2 ? kast2.naampad : null,
    kast3_uuid: kast3 ? kast3.uuid : null,
    kast3_naam: kast3 ? kast3.naam : null,
    kast3_naampad: kast3 ? kast3.naampad : null
  }
"""
        self.report = DQReport(name='report0230',
                               title='MIVModule met meerdere Wegkantkast bevestigingen',
                               datasource='ArangoDB',
                               persistent_column='N',
                               link_type='eminfra',
                               excel_filename='[RSA] MIVModule bevestigd aan meerdere kasten.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
