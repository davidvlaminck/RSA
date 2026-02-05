from lib.reports.DQReport import DQReport
from lib.connectors.OTLCursorPool import OTLCursorPool


class Report0043:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0043',
                               title='Instanties van deprecated classes',
                               spreadsheet_id='1rpYt_EKa5YOCDBdzmrAcV6vwoy3hccblR6_spaV2ziI',
                               datasource='PostGIS',
                               persistent_column='D')

        otl_cursor = OTLCursorPool.get_cursor()
        deprecated_classes = otl_cursor.execute("""
            SELECT o_c.uri
            FROM OSLOClass o_c
            WHERE o_c.deprecated_version IS NOT NULL AND o_c.deprecated_version != ""
        """).fetchall()

        self.report.result_query = """
            SELECT a.uuid AS asset_uuid, a_t.uri AS assettype_uri, a.toestand AS asset_toestand 
            FROM assets a
            INNER JOIN assettypes AS a_t ON (a.assettype = a_t.uuid)
            INNER JOIN (VALUES {}) AS d_c(uri) ON (a_t.uri = d_c.uri)
            WHERE a.actief = TRUE
        """.format(",".join(["('{}')".format(d[0]) for d in deprecated_classes]))

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET deprecated_keys = (
  FOR at IN assettypes
    FILTER at.uri IN [
      "https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#ContainerBuis",
      "https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#Deur",
      "https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#Betonfundering",
      "https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#Bijlage",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#MIVInstallatie",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Trappentoren",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Meetstation",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Matrixbord",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Baanlichaam",
      "https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Wegberm",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VRBAZ",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Damwand",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GeluidswerendeConstructie",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VRCommunicatiekaart",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VRBatterijICU",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Vluchtdeur",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Doorgang",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bovenbouw",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#FieldOfView",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Mantelbuis",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Toegangscontrole",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#OpgaandeBoom",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VRHandbediening",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ANPRCamera",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#VRStuurkaart",
      "https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Exoten",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefVoertuigOverhelling",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefSchokindexMVP",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefSchokindex",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefKerendVermogen",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefPerformantieniveau",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefBoomtoestand",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefWerkingsbreedteMVP",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefPerformantieklasse",
      "https://wegenenverkeer.data.vlaanderen.be/ns/proefenmeting#ProefWerkingsbreedteGC"]
    RETURN at._key
)

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
    AND a.assettype_key IN deprecated_keys

  LET at = FIRST(FOR t IN assettypes FILTER t._key == a.assettype_key LIMIT 1 RETURN t)

  SORT at.uri asc

  RETURN {
    asset_uuid: a._key,
    assettype_uri: at ? at.uri : null,
    asset_toestand: a.toestand
  }
"""