from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0101(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /* Report0101 - Vplan koppelingen (migrated to new datamodel)
         * New model: HeeftVPlan assetrelaties (relatietype_key=4738) with dienstdatum array
         * on the relation itself. VPlan is a separate asset (assettype_key=45d57fd0).
         * Bestekkoppelingen live in the bestekkoppelingen edge collection.
         */
        LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
        LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#ITSapp" LIMIT 1 RETURN at._key)
        LET hv_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HeeftVPlan" LIMIT 1 RETURN rt._key)

        FOR a IN assets
          FILTER a.assettype_key == vr1_key OR a.assettype_key == vr2_key

          /* LEFT JOIN HeeftVPlan relations */
          LET hv_rels = (
            FOR rel IN assetrelaties
              FILTER rel.relatietype_key == hv_key AND rel._from == a._id
              RETURN rel
          )

          /* PostGIS WHERE: (vplan IS NOT NULL AND actief=FALSE) OR actief=TRUE */
          FILTER (LENGTH(hv_rels) > 0 AND a.AIMDBStatus_isActief == false) OR a.AIMDBStatus_isActief == true

          /* bestekkoppelingen via edge collection - computed once per asset */
          LET active_bestekken = (
            FOR bk IN bestekkoppelingen
              FILTER bk._from == a._id
                AND CONTAINS(bk.DtcBestekkoppeling_status, "/actief")
              LET b = DOCUMENT(bk._to)
              FILTER b != null
              RETURN {
                  dossiernummer: b.eDeltaDossiernummer,
                  besteknummer: b.eDeltaBesteknummer,
                  aannemer: b.aannemerNaam
              }
          )

          /* For each relation (or 1 null if no relations) */
          FOR rel IN (LENGTH(hv_rels) > 0 ? hv_rels : [null])
            FILTER rel != null OR a.AIMDBStatus_isActief == true

            /* For each dienstdatum entry (or 1 null if no entries) */
            FOR ds IN (rel != null && rel['HeeftVPlan_dienstdatum'] != null && LENGTH(rel['HeeftVPlan_dienstdatum']) > 0 ? rel['HeeftVPlan_dienstdatum'] : [null])
              LET vplan = rel != null ? DOCUMENT(rel._to) : null

              FOR bk IN (LENGTH(active_bestekken) > 0 ? active_bestekken : [null])
                LET adres_json = (a.loc && a.loc.Locatie_puntlocatie && a.loc.Locatie_puntlocatie.DtcPuntlocatie_adres) ? a.loc.Locatie_puntlocatie.DtcPuntlocatie_adres : null
                LET provincie = adres_json && adres_json.DtcAdres_provincie ? adres_json.DtcAdres_provincie : null
                LET gemeente = adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null

                LET indienst = ds != null ? ds.DtcDienstdatum_indienstname : null
                LET uitdienst = ds != null ? ds.DtcDienstdatum_uitdienstname : null

                LET uitdienstdatum_formatted =
                  (indienst != null && uitdienst == null && LEFT(indienst, 10) <= DATE_NOW()) ? "in dienst" :
                  (indienst != null && uitdienst != null && DATE_NOW() >= LEFT(indienst, 10) && DATE_NOW() <= LEFT(uitdienst, 10)) ? "in dienst" :
                  (uitdienst != null ? LEFT(uitdienst, 10) : null)

                LET tien_jaar_oud = (uitdienst == null && indienst != null && DATE_DIFF(LEFT(indienst, 10), DATE_NOW(), "years") >= 10)

                LET dataconflicten = (
                  (vplan == null && a.AIMDBStatus_isActief == true && a.toestand == "in-gebruik") OR
                  (uitdienst == null && vplan != null && a.AIMDBStatus_isActief == true && a.toestand NOT IN ["in-gebruik", "overgedragen"]) OR
                  ((provincie == null || a.geometry == null) && a.AIMDBStatus_isActief == true)
                )

                SORT a.AIMDBStatus_isActief DESC, a.NaampadObject_naampad ASC, indienst DESC

                RETURN {
                  uuid: a._key,
                  installatie: REGEX_MATCHES(a.NaampadObject_naampad, '^[^/]{1,10}', false)[0],
                  naampad: a.NaampadObject_naampad,
                  actief: a.AIMDBStatus_isActief,
                  toestand: a.toestand,
                  adres_gemeente: gemeente,
                  adres_provincie: provincie,
                  indienstdatum: LEFT(indienst, 10),
                  uitdienstdatum: uitdienstdatum_formatted,
                  vplan_nr: vplan != null ? vplan.VPlan_plannummer : null,
                  vplan_nr_kort: vplan != null ? LEFT(vplan.VPlan_plannummer, 7) : null,
                  commentaar: ds != null ? ds.DtcDienstdatum_commentaar : null,
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