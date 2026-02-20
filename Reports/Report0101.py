from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0101(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0101',
                               title='Vplan koppelingen',
                               spreadsheet_id='17gA1IKf5VSF-HslE-C90l2msSNFzCsiakpcn-IlMDtI',
                               datasource='PostGIS',
                               link_type='eminfra',
                               persistent_column='R',
                               recalculate_cells=[('Dataconflicten', 'A1'), ('>10 jaar oud', 'A1')])

        self.report.result_query = """
            WITH vrs AS (
                SELECT
                    a.*,
                    l.geometry AS geom
                FROM assets a
                LEFT JOIN locatie l ON a.uuid = l.assetuuid
                WHERE a.assettype IN (
                    '13fa9473-f919-432a-bd00-bc19645bd30a',  -- Verkeersregelaar (Legacy)
                    '40f86745-ecaa-456b-8262-0a1f014602df'  -- ITSApp-RIS (Legacy)
                )
            )
            SELECT
                v.uuid,
                split_part(v.naampad, '/', 1) AS installatie,
                v.naampad,
                v.actief,
                v.toestand,
                l.adres_gemeente,
                l.adres_provincie,
                to_char(date(vplan.indienstdatum), 'yyyy-mm-dd') AS indienstdatum,
                CASE
                    WHEN vplan.uitdienstdatum IS NULL AND vplan.indienstdatum IS NOT NULL AND vplan.indienstdatum <= CURRENT_DATE THEN 'in dienst'
                    WHEN vplan.indienstdatum IS NOT NULL AND vplan.uitdienstdatum IS NOT NULL AND CURRENT_DATE BETWEEN vplan.indienstdatum AND vplan.uitdienstdatum THEN 'in dienst'
                    ELSE to_char(date(vplan.uitdienstdatum), 'yyyy-mm-dd')
                END AS uitdienstdatum,
                vplan.vplannummer AS vplan_nr,
                left(vplan.vplannummer, 7) AS vplan_nr_kort,
                vplan.commentaar,
                b.edeltadossiernummer,
                b.aannemernaam,
                (vplan.uitdienstdatum IS NULL AND vplan.indienstdatum <= CURRENT_DATE - INTERVAL '10 YEAR') AS "10_jaar_oud",
                CASE
                    WHEN vplan.uuid IS NULL AND v.actief = TRUE AND v.toestand = 'in-gebruik' THEN TRUE
                    WHEN vplan.uitdienstdatum IS NULL AND vplan.uuid IS NOT NULL AND v.actief = TRUE AND v.toestand NOT IN ('in-gebruik', 'overgedragen') THEN TRUE
                    WHEN (l.adres_provincie IS NULL OR l.geometry IS NULL) AND v.actief = TRUE THEN TRUE
                    ELSE FALSE
                END AS dataconflicten
            FROM vrs v
            LEFT JOIN locatie l ON v.uuid = l.assetuuid
            LEFT JOIN vplan_koppelingen vplan ON v.uuid = vplan.assetuuid
            LEFT JOIN bestekkoppelingen bk ON v.uuid = bk.assetuuid AND lower(bk.koppelingstatus) = 'actief'
            LEFT JOIN bestekken b ON bk.bestekuuid = b.uuid
            WHERE (vplan.uuid IS NOT NULL AND v.actief = FALSE) OR v.actief = TRUE
            ORDER BY v.actief DESC, dataconflicten, v.naampad, uitdienstdatum DESC;
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)

aql_query = """
/* Report0101 Vplankoppelingen */
LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#ITSApp-RIS" LIMIT 1 RETURN at._key)
LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#VRLegacy" LIMIT 1 RETURN at._key)

/* Select candidate assets, filter by assettype + active */
LET candidates = (
  FOR a IN assets
    FILTER
      a.AIMDBStatus_isActief == true
      AND
      (a.assettype_key == vr1_key OR a.assettype_key == vr2_key)

    /* Project only the fields we need later to keep memory small */
    RETURN {
      _key: a._key,
      naam: a.AIMNaamObject_naam,
      naampad: a.NaampadObject_naampad,
      naampad_parent: a.naampad_parent,
      toestand: a.toestand,
      loc: a.loc,
      bs: a.bs,
    }
)


/* 2) Iterate candidates
      For vplankoppelingenwe still may call DOCUMENT(...) for each vplankoppeling (these are fewer)
*/
FOR c IN candidates
  /* vplankoppelingen */
  FOR vplan IN vplankoppelingen
    FILTER vplan.asset_key == c._key
/*  LET vplankoppelingen = (
    FOR vplan IN vplankoppelingen
      FILTER vplan.asset_key == c._key
      RETURN {
        vplan_uuid: vplan.vplan_uuid,
        vplan_nummer: vplan.vplan_nummer,
        inDienstDatum: vplan.inDienstDatum,
        uitDienstDatum: vplan.uitDienstDatum
      }
  )*/
//  FILTER length(vplankoppelingen) > 0

  /* adres */
  LET adres_json = (c.loc && c.loc.Locatie_puntlocatie && c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres) ? c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres : null
  LET provincie = adres_json && adres_json.DtcAdres_provincie ? adres_json.DtcAdres_provincie : null
  LET gemeente = adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null
  LET adres_parts = [
    adres_json && adres_json.DtcAdres_straat ? adres_json.DtcAdres_straat : null,
    adres_json && adres_json.DtcAdres_nummer ? adres_json.DtcAdres_nummer : null,
    adres_json && adres_json.DtcAdres_bus ? adres_json.DtcAdres_bus : null,
    adres_json && adres_json.DtcAdres_postcode ? adres_json.DtcAdres_postcode : null,
    adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null
  ]
  LET adres_arr = (FOR p IN adres_parts FILTER p != null RETURN p)
  LET adres = LENGTH(adres_arr) > 0 ? CONCAT_SEPARATOR(" ", adres_arr) : null

  // bestekkoppelingen
  LET asset_bestekken = (
    FOR bk IN (c.bs && c.bs.Bestek_bestekkoppeling ? c.bs.Bestek_bestekkoppeling : [])
        FILTER bk != null AND bk._to != null
        LET b = DOCUMENT(bk._to)
        FILTER b != null
        RETURN {
            dossiernummer: b.eDeltaDossiernummer ? b.eDeltaDossiernummer : null,
            besteknummer: b.eDeltaBesteknummer ? b.eDeltaBesteknummer : null,
            aannemer: b.aannemerNaam ? b.aannemerNaam : null,
            van: bk.DtcBestekkoppeling_actiefVan ? bk.DtcBestekkoppeling_actiefVan : null,
            tot: bk.DtcBestekkoppeling_actiefTot ? bk.DtcBestekkoppeling_actiefTot : null
        }
    )
    LET meest_recent_bestek = asset_bestekken[0]

  /* Calculate jarenInDiendst */
  LET jarenInDienst =
    IS_NULL(vplan.uitDienstDatum)
      ? DATE_DIFF(left(vplan.inDienstDatum, 10), DATE_NOW(), "years")
      : DATE_DIFF(left(vplan.inDienstDatum, 10), left(vplan.uitDienstDatum, 10), "years")
  LET vplan_nummer_kort = vplan.vplan_nummer ? left(vplan.vplan_nummer, 7) : null

  RETURN {
    uuid: c._key,
    naam: c.naam,
    naampad: c.naampad,
    toestand: c.toestand,
    vplan_uuid: vplan.vplan_uuid,
    vplan_nummer: vplan.vplan_nummer,
    vplan_nummer_kort: vplan_nummer_kort,
    vplan_commentaar: null,
    inDienstDatum: vplan.inDienstDatum,
    uitDienstDatum: vplan.uitDienstDatum,
    jarenInDienst: jarenInDienst,
    provincie: provincie,
    gemeente: gemeente,
    adres: adres,
    //alle_bestekken: asset_bestekken,
    recent_bestek: meest_recent_bestek,
    recent_bestek_dossiernummer: meest_recent_bestek.dossiernummer,
    recent_bestek_aannemer: meest_recent_bestek.aannemer
  }
"""
