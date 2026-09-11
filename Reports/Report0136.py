from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0136(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0136',
                               title='Straatkolk heeft betrokkene relaties beheerder en verantwoordelijke-reiniging',
                               spreadsheet_id='1uYTd1vGSKMxxWbkbTjgpSo969ntXGj_-xXebBGXPdVY',
                               datasource='ArangoDB',
                               persistent_column='G',
                               excel_filename='[RSA] Straatkolk heeft betrokkene relaties beheerder en verantwoordelijke-reiniging.xlsx',
                               )

        self.report.result_query = """
            FOR a IN assets
              FILTER a.assettype_key == "a5c7c355"
              FILTER a.AIMDBStatus_isActief == true
              LET assettype = DOCUMENT(CONCAT("assettypes/", a.assettype_key))
              LET beheerder = FIRST(
                FOR b IN betrokkenerelaties
                  FILTER b._from == a._id AND b.rol == "beheerder"
                  LET agent = DOCUMENT(b._to)
                  FILTER agent != null AND agent.AIMDBStatus_isActief == true
                  RETURN agent.purl.Agent_naam
              )
              LET verantwoordelijke_reiniging = FIRST(
                FOR b IN betrokkenerelaties
                  FILTER b._from == a._id AND b.rol == "verantwoordelijke-reiniging"
                  LET agent = DOCUMENT(b._to)
                  FILTER agent != null AND agent.AIMDBStatus_isActief == true
                  RETURN agent.purl.Agent_naam
              )
              FILTER beheerder == null OR (beheerder != null AND !REGEX_TEST(beheerder, '^district', true) AND verantwoordelijke_reiniging == null)
              SORT a.loc.Locatie_puntlocatie.DtcPuntlocatie_weglocatie.DtcWeglocatie_ident2 ASC, a.loc.Locatie_puntlocatie.DtcPuntlocatie_weglocatie.DtcWeglocatie_ident8 ASC, beheerder ASC, verantwoordelijke_reiniging ASC
              RETURN {
                uuid: a._key,
                assettype_uri: assettype.uri,
                ident2: a.loc.Locatie_puntlocatie.DtcPuntlocatie_weglocatie.DtcWeglocatie_ident2,
                ident8: a.loc.Locatie_puntlocatie.DtcPuntlocatie_weglocatie.DtcWeglocatie_ident8,
                beheerder: beheerder,
                verantwoordelijke_reiniging: verantwoordelijke_reiniging
              }
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
