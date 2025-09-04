from DQReport import DQReport


class Report0031:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0031',
                               title="Netwerkelementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
                               spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
                               datasource='PostGIS',
                               persistent_column='D',
                               link_type='eminfra_onderdeel')

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

# aql_query = """
# FOR n IN assets
#   FILTER n.assettype_key == "b6f86b8d"   // Netwerkelement
#     AND n.AIMDBStatus_isActief == TRUE
#     AND n.Netwerkelement_gebruik == 'https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkelemGebruik/l2-switch'
#
#   // Traverse 1 hop OUTBOUND to see if there is a HoortBij relation to an L2AccessStructuur
#   LET heeftRelatie = LENGTH(
#     FOR v, rel IN OUTBOUND n assetrelaties
#       FILTER rel.relatietype_key == "812d" // HoortBij
#         AND v.assettype_key == "30b571a9"   // L2AccessStructuur
#         AND v.AIMDBStatus_isActief == TRUE
#       RETURN 1
#   ) > 0
#
#   FILTER heeftRelatie == false
#
#   RETURN {
#     uuid: n._key,
#     naam: n.AIMNaamObject_naam,
#     gebruik: n.Netwerkelement_gebruik
#   }
# """