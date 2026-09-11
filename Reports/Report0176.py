from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0176(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        FOR a1 IN assets
          FILTER a1.assettype_key == "615356ae"
          FILTER a1.AIMDBStatus_isActief == true
          FILTER HAS(a1, "geometry")
          FOR a2 IN assets
            FILTER a2.assettype_key == "615356ae"
            FILTER a2.AIMDBStatus_isActief == true
            FILTER HAS(a2, "geometry")
            FILTER a1._key != a2._key
            LET dist = DISTANCE(a1.geometry.coordinates[1], a1.geometry.coordinates[0], a2.geometry.coordinates[1], a2.geometry.coordinates[0])
            FILTER dist <= 5
            RETURN {
              g1_uuid: a1._key,
              g1_toestand: SPLIT(a1.AIMToestand_toestand, '/')[-1],
              g1_naam: a1.AIMNaamObject_naam,
              g1_commentaar: a1.AIMObject_notitie,
              g2_uuid: a2._key,
              g2_toestand: SPLIT(a2.AIMToestand_toestand, '/')[-1],
              g2_naam: a2.AIMNaamObject_naam,
              g2_commentaar: a2.AIMObject_notitie,
              afstand: FLOOR(dist * 100) / 100
            }
        """

        self.report = DQReport(name='report0176', title='Dubbele assets op kruispunt: Galgpaal, Seinbrug, Boogpaal, Rechte Steun',
                               spreadsheet_id='1F9BXJrnr-hdoLnQ9L7UctGF16IyUQqlV7hRJzy1WlO0', datasource='ArangoDB',
                               persistent_column='',
                               excel_filename='[RSA] Dubbele assets op kruispunt_ Galgpaal, Seinbrug, Boogpaal, Rechte Steun.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
