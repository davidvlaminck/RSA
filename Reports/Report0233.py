from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0233(BaseReport):
    def init_report(self) -> None:
        aql_query = """
/*
eWKT tekst string overschrijdt geen 30000 karakters in lengte
*/
FOR asset IN assets
FILTER asset.AIMDBStatus_isActief == true
LET is_otl = STARTS_WITH(asset["@type"], 'https://wegenenverkeer.data.vlaanderen.be', true)
FILTER is_otl

LET wkt = asset.wkt
LET wkt_nbr_characters = LENGTH(wkt)
FILTER wkt_nbr_characters >= 30000

LET locatie = asset.loc && asset.loc.Locatie_geometrie ? asset.loc.Locatie_geometrie : null

LET geometrie = asset.geo && asset.geo.Geometrie_log[0] && asset.geo.Geometrie_log[0].DtcLog_geometrie ? asset.geo.Geometrie_log[0].DtcLog_geometrie : null

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
'wkt': wkt,
'wkt_nbr_characters': wkt_nbr_characters,
'toezichter': toezichter.purl.Agent_naam ? toezichter.purl.Agent_naam : null,
'toezichtsgroep': toezichtsgroep.purl.Agent_naam ? toezichtsgroep.purl.Agent_naam : null,
}
        """

        self.report = DQReport(name='report0233',
                               title='eWKT tekst string overschrijdt geen 30000 karakters qua lengte',
                               datasource='ArangoDB',
                               persistent_column='K',
                               link_type='eminfra',
                               excel_filename='[RSA] eWKT tekst string overschrijdt geen 30000 karakters qua lengte.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
