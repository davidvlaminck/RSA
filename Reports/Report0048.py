from DQReport import DQReport


class Report0048:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0048',
                               title='BitumineuzeLaag heeft steeds een LigtOp relatie naar een Onderbouw. Wanneer niet aan deze voorwaarde voldaan is, geeft dit rapport een aantal suggesties voor Onderbouwen adhv de geometrie.',
                               spreadsheet_id='',
                               datasource='PostGIS',
                               persistent_column='C')

        self.report.result_query = """
            WITH a_bl as (
                SELECT a.uuid, g.wkt_string
                FROM assets a
                INNER JOIN assettypes a_t ON (a.assettype = a_t.uuid)
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BitumineuzeLaag')
            , a_ob AS (
                SELECT a.uuid , g.wkt_string 
                FROM assets a
                INNER JOIN assettypes a_t ON (a.assettype = a_t.uuid)
                INNER JOIN geometrie g ON (g.assetuuid = a.uuid)
                WHERE a_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Onderbouw')
            SELECT a_bl.uuid AS uuid_bitumineuze_laag, a_ob.uuid AS uuid_suggested_onderbouw
            FROM a_bl, a_ob
            WHERE NOT EXISTS (
                SELECT 1
                FROM assetrelaties a_r
                INNER JOIN relatietypes r_t ON (a_r.relatietype = r_t.uuid)
                WHERE a_r.bronuuid = a_bl.uuid AND r_t.uri = 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LigtOp'
                LIMIT 1
            ) AND ST_Intersects(ST_GeogFromText(a_bl.wkt_string), ST_GeogFromText(a_ob.wkt_string))
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
