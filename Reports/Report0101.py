from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0101(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#ITSApp-RIS" LIMIT 1 RETURN at._key)
        LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#VRLegacy" LIMIT 1 RETURN at._key)

        FOR a IN assets
          FILTER a.assettype_key == vr1_key OR a.assettype_key == vr2_key

          /* LEFT JOIN vplankoppelingen: elke vplan wordt een aparte rij, ook actieve assets zonder vplan */
          LET vplans = (
            FOR vplan IN vplankoppelingen
              FILTER vplan.asset_key == a._key
              RETURN vplan
          )
          /* PostGIS WHERE: (vplan IS NOT NULL AND actief=FALSE) OR actief=TRUE */
          FILTER (LENGTH(vplans) > 0 AND a.AIMDBStatus_isActief == false) OR a.AIMDBStatus_isActief == true

          /* LEFT JOIN bestekkoppelingen (actief) - ook vermenigvuldigen zoals PostGIS */
          LET active_bestekken = (
            FOR bk IN (a.bs && a.bs.Bestek_bestekkoppeling ? a.bs.Bestek_bestekkoppeling : [])
                FILTER bk != null AND bk._to != null AND RIGHT(bk.DtcBestekkoppeling_status, 7) == "/actief"
                LET b = DOCUMENT(bk._to)
                FILTER b != null
                RETURN {
                    dossiernummer: b.eDeltaDossiernummer,
                    besteknummer: b.eDeltaBesteknummer,
                    aannemer: b.aannemerNaam
                }
          )

          /* Voor elke vplan (of 1x null als actief zonder vplan) */
          FOR vplan IN (LENGTH(vplans) > 0 ? vplans : [null])
            FILTER vplan != null OR a.AIMDBStatus_isActief == true

            /* Voor elke actieve bestekkoppeling (of 1x null als geen bestek) */
            FOR bk IN (LENGTH(active_bestekken) > 0 ? active_bestekken : [null])

              /* adres */
              LET adres_json = (a.loc && a.loc.Locatie_puntlocatie && a.loc.Locatie_puntlocatie.DtcPuntlocatie_adres) ? a.loc.Locatie_puntlocatie.DtcPuntlocatie_adres : null
              LET provincie = adres_json && adres_json.DtcAdres_provincie ? adres_json.DtcAdres_provincie : null
              LET gemeente = adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null

              /* uitdienstdatum */
              LET uitdienstdatum_formatted =
                (vplan.uitDienstDatum == null && vplan.inDienstDatum != null && LEFT(vplan.inDienstDatum, 10) <= DATE_NOW()) ? "in dienst" :
                (vplan.inDienstDatum != null && vplan.uitDienstDatum != null && DATE_NOW() >= LEFT(vplan.inDienstDatum, 10) && DATE_NOW() <= LEFT(vplan.uitDienstDatum, 10)) ? "in dienst" :
                (vplan.uitDienstDatum != null ? LEFT(vplan.uitDienstDatum, 10) : null)

              /* 10_jaar_oud */
              LET tien_jaar_oud = (vplan.uitDienstDatum == null && vplan.inDienstDatum != null && DATE_DIFF(LEFT(vplan.inDienstDatum, 10), DATE_NOW(), "years") >= 10)

              /* dataconflicten */
              LET dataconflicten = (
                (vplan == null && a.AIMDBStatus_isActief == true && a.toestand == "in-gebruik") OR
                (vplan.uitDienstDatum == null && vplan != null && a.AIMDBStatus_isActief == true && a.toestand NOT IN ["in-gebruik", "overgedragen"]) OR
                ((provincie == null || a.geometry == null) && a.AIMDBStatus_isActief == true)
              )

              SORT a.AIMDBStatus_isActief DESC, a.NaampadObject_naampad ASC, vplan.inDienstDatum DESC

              RETURN {
                uuid: a._key,
                installatie: REGEX_MATCHES(a.NaampadObject_naampad, '^[^/]{1,10}', false)[0],
                naampad: a.NaampadObject_naampad,
                actief: a.AIMDBStatus_isActief,
                toestand: a.toestand,
                adres_gemeente: gemeente,
                adres_provincie: provincie,
                indienstdatum: LEFT(vplan.inDienstDatum, 10),
                uitdienstdatum: uitdienstdatum_formatted,
                vplan_nr: vplan.vplan_nummer,
                vplan_nr_kort: LEFT(vplan.vplan_nummer, 7),
                commentaar: 'onbeschikbaar',
                edeltadossiernummer: bk.dossiernummer,
                aannemernaam: bk.aannemer,
                tien_jaar_oud: tien_jaar_oud,
                dataconflicten: dataconflicten
              }
        """

        self.report = DQReport(name='report0101',
                               title='Vplan koppelingen',
                               spreadsheet_id='17gA1IKf5VSF-HslE-C90l2msSNFzCsiakpcn-IlMDtI',
                               datasource='ArangoDB',
                               link_type='eminfra',
                               persistent_column='R',
                               recalculate_cells=[('Dataconflicten', 'A1'), ('>10 jaar oud', 'A1')],
                               excel_filename='[Vplan] Vplan data EM-Infra.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
