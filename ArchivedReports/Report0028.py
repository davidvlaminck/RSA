from lib.reports.DQReport import DQReport


class Report0028:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0028',
                               title='IP Netwerkelementen (niet OTN) hebben een HoortBij relatie met een legacy object van type IP',
                               spreadsheet_id='1wn05XDV1PkyVdGgDEO3yUU0Jqf3t6asGH0SyGXQQWS8',
                               datasource='PostGIS',
                               persistent_column='D',
                               link_type='eminfra_onderdeel')

        self.report.result_query = """
            -- CTE selecteert actieve assets van het type Netwerkelement met een specifiek merk (niet NULL, NOKIA, Ciena, edge)
            WITH cte_asset_netwerkelement AS (
                SELECT 
                    assets.uuid, 
                    assets.naam, 
                    a.waarde AS merk
                FROM 
                    assets 
                LEFT JOIN 
                    attribuutwaarden a ON a.assetuuid = assets.uuid 
                    AND a.attribuutuuid = 'a88f8ffe-2d15-48a6-872e-e74b72d20591'  -- merk
                WHERE 
                    assets.assettype = 'b6f86b8d-543d-4525-8458-36b498333416'  -- Netwerkelement
                    AND assets.actief = TRUE 
                    AND (a.waarde IS NULL OR a.waarde NOT IN (
                        'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NULL', 
                        'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NOKIA', 
                        'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/Ciena', 
                        'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/edge'
                    ))
            ),
            -- CTE telt het aantal HoortBij-relaties naar IP-netwerkapparatuur (legacy)
            cte_asset_relationship_counts AS (
                SELECT 
                    n.uuid, 
                    COUNT(assets.uuid) AS aantal
                FROM 
                    cte_asset_netwerkelement n
                LEFT JOIN 
                    assetrelaties ar ON n.uuid = ar.bronuuid 
                    AND ar.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'  -- HoortBij-relatie
                LEFT JOIN 
                    assets ON ar.doeluuid = assets.uuid 
                    AND assets.actief = TRUE
                    AND assets.assettype = '5454b9b1-1bf4-4096-a124-1e3aeee725a2'  -- IP-netwerkapparatuur (legacy)
                GROUP BY
                    n.uuid
            )
            -- Main query: Select assets with no related 'IPS' assets
            SELECT 
                n.uuid, 
                n.naam, 
                n.merk
            FROM 
                cte_asset_netwerkelement n
            LEFT JOIN 
                cte_asset_relationship_counts r ON n.uuid = r.uuid
            WHERE 
                r.aantal = 0;
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
