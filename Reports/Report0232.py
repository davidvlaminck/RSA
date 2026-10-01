from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0232(BaseReport):
    def init_report(self) -> None:
        aql_query = """
/*
Actieve OTL-asset heeft een locatie (lgc), maar geen geometrie (otl) kenmerk
*/
FOR asset IN assets
  FILTER asset.AIMDBStatus_isActief == true
  LET is_otl = STARTS_WITH(asset["@type"], 'https://wegenenverkeer.data.vlaanderen.be', true)
  FILTER is_otl

  LET locatie = asset.loc && asset.loc.Locatie_geometrie ? asset.loc.Locatie_geometrie : null
  FILTER locatie != null

  LET geometrie = asset.geo && asset.geo.Geometrie_log[0] && asset.geo.Geometrie_log[0].DtcLog_geometrie ? asset.geo.Geometrie_log[0].DtcLog_geometrie : null
  FILTER geometrie == null
  
    /* Pre-fetch toezichter and toezichtsgroep in a single traversal */
  LET betrokkenen = (
    FOR v, e IN 1..1 OUTBOUND asset betrokkenerelaties
      FILTER e.rol IN ['toezichter', 'toezichtsgroep']
      RETURN { rol: e.rol, agent: v }
  )

  /* Extract toezichter and toezichtsgroep from betrokkenen */
  LET toezichter = FIRST(FOR b IN betrokkenen FILTER b.rol == 'toezichter' RETURN b.agent)
  LET toezichtsgroep = FIRST(FOR b IN betrokkenen FILTER b.rol == 'toezichtsgroep' RETURN b.agent)

  RETURN {
    'assetId_identificator': asset._key,
    'typeURI': asset["@type"],
  	'naam': asset.AIMNaamObject_naam,
  	'naampad': asset.NaampadObject_naampad,
  	'locatie': locatie,
  	'geometrie': geometrie,
  	'toezichter': toezichter.purl.Agent_naam ? toezichter.purl.Agent_naam : null,
    'toezichtsgroep': toezichtsgroep.purl.Agent_naam ? toezichtsgroep.purl.Agent_naam : null,
  }
        """

        self.report = DQReport(name='report0232',
                               title='OTL assets hebben naast het locatie (lgc) eveneens het geometrie (OTL) kenmerk',
                               datasource='ArangoDB',
                               persistent_column='I',
                               link_type='eminfra',
                               excel_filename='[RSA] OTL assets hebben naast het locatie (lgc) eveneens het geometrie (OTL) kenmerk.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
