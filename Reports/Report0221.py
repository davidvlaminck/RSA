from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0221(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /* Report0221: Wegverlichtingsinstallatie (Legacy) heeft steeds een locatie */
        LET wv_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#WV" LIMIT 1 RETURN at._key)
        
        /* Select assets, filter by assettype + active + locatie */
        FOR a IN assets
          FILTER
            a.assettype_key == wv_key
            AND a.AIMDBStatus_isActief == true
            AND a.loc.Locatie_geometrie == null
        
          LET toezichter = (a.tz && a.tz.Toezicht_toezichter && a.tz.Toezicht_toezichter.DtcToezichter_email) ? a.tz.Toezicht_toezichter.DtcToezichter_email : null
          LET toezichtgroep = (a.tz && a.tz.Toezicht_toezichtgroep && a.tz.Toezicht_toezichtgroep.DtcToezichtGroep_naam) ? a.tz.Toezicht_toezichtgroep.DtcToezichtGroep_naam : null
          LET schadebeheerder = (a.tz && a.tz.Schadebeheerder_schadebeheerder && a.tz.Schadebeheerder_schadebeheerder.DtcBeheerder_naam) ? a.tz.Schadebeheerder_schadebeheerder.DtcBeheerder_naam : null
          LET schadebeheerder_referentie = (a.tz && a.tz.Schadebeheerder_schadebeheerder && a.tz.Schadebeheerder_schadebeheerder.DtcBeheerder_referentie) ? a.tz.Schadebeheerder_schadebeheerder.DtcBeheerder_referentie : null
        
          RETURN {
            _key: a._key,
            naam: a.AIMNaamObject_naam,
            naampad: a.NaampadObject_naampad,
            toestand: a.toestand,
            toezichter: toezichter,
            toezichtsgroep: toezichtgroep,
            schadebeheerder: schadebeheerder
          }
        """
        self.report = DQReport(name='report0221',
                               title='Wegverlichtingsinstallatie (Legacy) heeft steeds een locatie',
                               spreadsheet_id='1A8jalizscvlw4MzncK3fxnkOzVc1pK0GgeyP3BhLRnY',
                               datasource='ArangoDB',
                               persistent_column='H')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
