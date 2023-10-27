from DQReport import DQReport


class Report0028:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0028',
                               title='IP Netwerkelementen (niet OTN) hebben een HoortBij relatie met een legacy object van type IP',
                               spreadsheet_id='1wn05XDV1PkyVdGgDEO3yUU0Jqf3t6asGH0SyGXQQWS8',
                               datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
            WITH n AS (
                SELECT assets.uuid, assets.naam, a.waarde AS merk
                FROM assets 
                    LEFT JOIN attribuutwaarden a ON a.assetuuid = assets.uuid 
                        AND a.attribuutuuid = 'a88f8ffe-2d15-48a6-872e-e74b72d20591'
                WHERE assettype = 'b6f86b8d-543d-4525-8458-36b498333416' AND assets.actief = TRUE AND 
                    (a.waarde NOT IN ('https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NULL', 
                    'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NOKIA', 
                    'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/Ciena', 
                    'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/edge') OR a.waarde is NULL)),
            relaties_met_ips AS (
                SELECT n.uuid, COUNT(assets.uuid) AS aantal 
                FROM n
                    LEFT JOIN assetrelaties ar ON n.uuid = ar.bronuuid 
                        AND ar.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
                    LEFT JOIN assets ON ar.doeluuid = assets.uuid AND assets.actief = TRUE 
                        AND assets.assettype = '5454b9b1-1bf4-4096-a124-1e3aeee725a2' 
                GROUP BY 1)
            SELECT n.uuid, n.naam, n.merk
            FROM n
                LEFT JOIN relaties_met_ips r ON n.uuid = r.uuid
            WHERE r.aantal = 0;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
