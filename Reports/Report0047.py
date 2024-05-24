from DQReport import DQReport


class Report0047:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0047',
                               title='Wanneer een BitumineuzeLaag geometrisch op een Onderbouw ligt, dan zijn deze '
                                     'assets verbonden door een LigtOp relatie van BitumineuzeLaag naar Onderbouw.',
                               spreadsheet_id='1BiRG3GxXF1AjpAoCWW_O7ukg2WeCEvGnhew-_YuclrQ',
                               datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
WITH a_bl as (
    SELECT a.uuid, ST_GeomFromText(wkt_string) AS geom
    FROM assets a
        INNER JOIN assettypes a_t ON a.assettype = a_t.uuid
        INNER JOIN geometrie g ON g.assetuuid = a.uuid
    WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BitumineuzeLaag' AND a.actief = TRUE)
, a_ob AS (
    SELECT a.uuid, ST_GeomFromText(wkt_string) AS geom
    FROM assets a
        INNER JOIN assettypes a_t ON a.assettype = a_t.uuid
        INNER JOIN geometrie g ON g.assetuuid = a.uuid
    WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Onderbouw' AND a.actief = TRUE)
SELECT a_bl.uuid AS uuid_bitumineuze_laag, a_ob.uuid AS uuid_onderbouw 
FROM a_bl
    INNER JOIN a_ob ON ST_Intersects(a_bl.geom, a_ob.geom)
    LEFT JOIN assetrelaties ON (bronuuid = a_bl.uuid AND doeluuid = a_ob.uuid AND assetrelaties.relatietype = '321c18b8-92ca-4188-a28a-f00cdfaa0e31' AND assetrelaties.actief = TRUE) -- LigtOp
WHERE assetrelaties.doeluuid IS NULL;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
