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
                SELECT a.uuid, g.wkt_string
                FROM assets a
                INNER JOIN assettypes a_t ON (a.assettype = a_t.uuid)
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BitumineuzeLaag')
            , a_ob AS (
                SELECT a.uuid, g.wkt_string 
                FROM assets a
                INNER JOIN assettypes a_t ON (a.assettype = a_t.uuid)
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Onderbouw')
            SELECT a_bl_prime.uuid AS uuid_bitumineuze_laag, a_ob_prime.uuid AS uuid_onderbouw
            FROM a_bl AS a_bl_prime, a_ob AS a_ob_prime
            WHERE ST_Intersects(ST_GeogFromText(a_bl_prime.wkt_string), ST_GeogFromText(a_ob_prime.wkt_string))
            AND NOT EXISTS (
                SELECT 1
                FROM a_bl, a_ob
                INNER JOIN assetrelaties a_r ON (a_r.bronuuid = a_bl_prime.uuid AND a_r.doeluuid = a_ob_prime.uuid)
                INNER JOIN relatietypes r_t ON (a_r.relatietype = r_t.uuid)
                WHERE r_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LigtOp'
                LIMIT 1
            )
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
