from DQReport import DQReport


class Report0031:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0031',
                               title="Netwerkelementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
                               spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
                               datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
            -- Netwerkementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur
            WITH elementen AS (
                SELECT a.*, aw.waarde as gebruik 
                FROM assets a
                left join attribuutwaarden aw on a.uuid = aw.assetuuid and aw.attribuutuuid = '63ac54e9-8ea4-4e0f-8c5d-d7891a7af811' -- attribuut gebruik
                where
                    a.assettype = 'b6f86b8d-543d-4525-8458-36b498333416' -- Netwerkelement
                    AND a.actief = true 
                    and	aw.waarde like '%/l2-switch' -- attribuutwaarde gebruik komt overeen met l2-switch (einde van de URI)
                ), 
            relaties AS (
                SELECT assetrelaties.*
                FROM assetrelaties
                    LEFT JOIN assets ON assets.uuid = doeluuid AND assets.actief = TRUE AND assets.assettype = '30b571a9-77ef-4289-a458-139882a5e97a' -- L2AccessStructuur
                    left join relatietypes on assetrelaties.relatietype = relatietypes."uuid" 
                WHERE relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2') -- HoortBij
            SELECT elementen.uuid, elementen.naam, elementen.gebruik
            FROM elementen
            LEFT JOIN relaties ON elementen.uuid = relaties.bronuuid
            WHERE relaties.uuid IS NULL;  -- Hoortbij Relatie ontbreekt
            """
    def run_report(self, sender):
        self.report.run_report(sender=sender)
