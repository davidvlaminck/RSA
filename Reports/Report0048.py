from DQReport import DQReport


class Report0048:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0048',
                               title='(Experimenteel) Wanneer een BitumineuzeLaag geen LigtOpt relatie heeft naar een Onderbouw, welke Onderbouw(en) liggen dan geometrisch onder deze BitumineuzeLaag.',
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
            SELECT a_bl.uuid AS uuid_bitum_missing, a_ob.uuid AS uuid_onder_suggestie
            FROM a_bl, a_ob
            WHERE NOT EXISTS (
                SELECT 1
                FROM assetrelaties a_r
                WHERE a_r.bronuuid = a_bl.uuid AND a_r.relatietype = '321c18b8-92ca-4188-a28a-f00cdfaa0e31'
            ) AND ST_Intersects(ST_GeogFromText(a_bl.wkt_string), ST_GeogFromText(a_ob.wkt_string))
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
