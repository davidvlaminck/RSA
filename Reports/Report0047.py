from DQReport import DQReport


class Report0047:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0047',
                               title='(Experimenteel) Wanneer een BitumineuzeLaag geometrisch op een Onderbouw ligt, dan is er een LigtOp relatie van die BitumineuzeLaag naar die Onderbouw.',
                               spreadsheet_id='',
                               datasource='PostGIS',
                               persistent_column='C')

        self.report.result_query = """
            WITH a_bl AS (
                SELECT *
                FROM assets a
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a.assettype = '3d24792a-6941-481b-9c8c-739309fd3ffb')
            , a_ob AS (
                SELECT *
                FROM assets a
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a.assettype = '3d24792a-6941-481b-9c8c-739309fd3ffb')
            SELECT a_bl_prime.uuid AS uuid_bitumineuze_laag, a_ob_prime AS uuid_onderbouw
            FROM a_bl AS a_bl_prime, a_ob AS a_ob_prime
            WHERE ST_Intersects(ST_GeogFromText(a_bl_prime.wkt_string), ST_GeogFromText(a_ob_prime.wkt_string))
            AND NOT exists (
                SELECT 1
                FROM a_bl, a_ob
                INNER JOIN assetrelaties a_r ON (a_r.bronuuid = a_bl_prime.uuid AND a_r.doeluuid = a_ob_prime.uuid)
                WHERE a_r.relatietype = '321c18b8-92ca-4188-a28a-f00cdfaa0e31'
                LIMIT 1
            )
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
