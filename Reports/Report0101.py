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
                               recalculate_cells=[('Dataconflicten', 'A1'), ('>10 jaar oud', 'A1')],
                               excel_filename='[Vplan] Vplan data EM-Infra.xlsx',)

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
      actief: a.AIMDBStatus_isActief,
      naam: a.AIMNaamObject_naam,
      naampad: a.NaampadObject_naampad,
      naampad_parent: a.naampad_parent,
      toestand: a.toestand,
      loc: a.loc,
      bs: a.bs
    }
)


/* 2) Iterate candidates */
FOR c IN candidates
  /* vplankoppelingen */
  FOR vplan IN vplankoppelingen
    FILTER vplan.asset_key == c._key

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

    /* bestekkoppelingen */
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
    LET meest_recent_bestek = (LENGTH(asset_bestekken) > 0 ? asset_bestekken[0] : null)

    /* Calculate jarenInDienst */
    LET jarenInDienst =
      IS_NULL(vplan.uitDienstDatum)
        ? DATE_DIFF(LEFT(vplan.inDienstDatum, 10), DATE_NOW(), "years")
        : DATE_DIFF(LEFT(vplan.inDienstDatum, 10), LEFT(vplan.uitDienstDatum, 10), "years")
    LET vplan_nummer_kort = vplan.vplan_nummer ? LEFT(vplan.vplan_nummer, 7) : null
    LET tien_jaar_oud = jarenInDienst >= 10

    SORT c.AIMDBStatus_isActief DESC, c.naampad ASC, vplan.inDienstDatum DESC

    RETURN {
      uuid: c._key,
      installatie: (c.naampad ? regex_matches(c.naampad, '^[^/]{1,10}', false)[0] : null),
      naampad: c.naampad,
      actief: c.AIMDBStatus_isActief,
      toestand: c.toestand,
      adres_gemeente: gemeente,
      adres_provincie: provincie,
      indienstdatum: vplan.inDienstDatum,
      uitdienstdatum: vplan.uitDienstDatum,
      vplan_nr: vplan.vplan_nummer,
      vplan_nr_kort: vplan_nummer_kort,
      commentaar: (vplan.commentaar ? vplan.commentaar : 'onbeschikbaar'),
      edeltadossiernummer: (meest_recent_bestek != null ? meest_recent_bestek.dossiernummer : null),
      aannemernaam: (meest_recent_bestek != null ? meest_recent_bestek.aannemer : null),
      tien_jaar_oud: tien_jaar_oud,
      dataconflicten: null,
      debug_asset_bestekken_is_array: IS_ARRAY(asset_bestekken),
      debug_asset_bestekken_is_obj: IS_OBJECT(asset_bestekken),
      debug_meest_recent_is_obj: IS_OBJECT(meest_recent_bestek),
      debug_meest_recent_is_null: IS_NULL(meest_recent_bestek)

    }
"""

aql_debug_query = """
/* Debug variant: compute the same result rows, then for first 10 rows return attribute-level type info */
LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#ITSApp-RIS" LIMIT 1 RETURN at._key)
LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#VRLegacy" LIMIT 1 RETURN at._key)

LET candidates = (
  FOR a IN assets
    FILTER a.AIMDBStatus_isActief == true
      AND (a.assettype_key == vr1_key OR a.assettype_key == vr2_key)
    RETURN {
      _key: a._key,
      actief: a.AIMDBStatus_isActief,
      naam: a.AIMNaamObject_naam,
      naampad: a.NaampadObject_naampad,
      naampad_parent: a.naampad_parent,
      toestand: a.toestand,
      loc: a.loc,
      bs: a.bs
    }
)

LET rows = (
  FOR c IN candidates
    FOR vplan IN vplankoppelingen
      FILTER vplan.asset_key == c._key

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
      LET meest_recent_bestek = (LENGTH(asset_bestekken) > 0 ? asset_bestekken[0] : null)

      LET jarenInDienst =
        IS_NULL(vplan.uitDienstDatum)
          ? DATE_DIFF(LEFT(vplan.inDienstDatum, 10), DATE_NOW(), "years")
          : DATE_DIFF(LEFT(vplan.inDienstDatum, 10), LEFT(vplan.uitDienstDatum, 10), "years")
      LET vplan_nummer_kort = vplan.vplan_nummer ? LEFT(vplan.vplan_nummer, 7) : null
      LET tien_jaar_oud = jarenInDienst >= 10

      SORT c.AIMDBStatus_isActief DESC, c.naampad ASC, vplan.inDienstDatum DESC

      RETURN {
        uuid: c._key,
        installatie: (c.naampad ? regex_matches(c.naampad, '^[^/]{1,10}', false)[0] : null),
        naampad: c.naampad,
        actief: c.AIMDBStatus_isActief,
        toestand: c.toestand,
        adres_gemeente: gemeente,
        adres_provincie: provincie,
        indienstdatum: vplan.inDienstDatum,
        uitdienstdatum: vplan.uitDienstDatum,
        vplan_nr: vplan.vplan_nummer,
        vplan_nr_kort: vplan_nummer_kort,
        commentaar: (vplan.commentaar ? vplan.commentaar : 'onbeschikbaar'),
        edeltadossiernummer: (meest_recent_bestek != null ? meest_recent_bestek.dossiernummer : null),
        aannemernaam: (meest_recent_bestek != null ? meest_recent_bestek.aannemer : null),
        tien_jaar_oud: tien_jaar_oud,
        dataconflicten: null,
        debug_asset_bestekken_is_array: IS_ARRAY(asset_bestekken),
        debug_asset_bestekken_is_obj: IS_OBJECT(asset_bestekken),
        debug_meest_recent_is_obj: IS_OBJECT(meest_recent_bestek),
        debug_meest_recent_is_null: IS_NULL(meest_recent_bestek)
      }
)

/* For debugging: return the first 10 rows with per-attribute type checks */
RETURN (
  FOR r IN SLICE(rows, 0, 10)
    LET attrs = (
      FOR k IN ATTRIBUTES(r)
        LET v = r[k]
        RETURN {
          key: k,
          typeof: (
            IS_OBJECT(v) ? 'object' : (
            IS_ARRAY(v) ? 'array' : (
            IS_STRING(v) ? 'string' : (
            IS_NUMBER(v) ? 'number' : (
            IS_BOOL(v) ? 'bool' : (
            IS_NULL(v) ? 'null' : 'other')))))) ,
          isNull: IS_NULL(v),
          isString: IS_STRING(v),
          isNumber: IS_NUMBER(v),
          isBool: IS_BOOL(v),
          isArray: IS_ARRAY(v),
          isObject: IS_OBJECT(v)
        }
    )
    RETURN { uuid: r.uuid, attrs: attrs }
)
"""

aql_safe_query = """
/* Safe variant: compute rows, then for each row convert ARRAY/OBJECT values to JSON strings so rows are CSV-friendly. Returns all rows (not limited). */
LET vr1_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#ITSApp-RIS" LIMIT 1 RETURN at._key)
LET vr2_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#VRLegacy" LIMIT 1 RETURN at._key)

LET candidates = (
  FOR a IN assets
    FILTER a.AIMDBStatus_isActief == true
      AND (a.assettype_key == vr1_key OR a.assettype_key == vr2_key)
    RETURN {
      _key: a._key,
      actief: a.AIMDBStatus_isActief,
      naam: a.AIMNaamObject_naam,
      naampad: a.NaampadObject_naampad,
      naampad_parent: a.naampad_parent,
      toestand: a.toestand,
      loc: a.loc,
      bs: a.bs
    }
)

LET rows = (
  FOR c IN candidates
    FOR vplan IN vplankoppelingen
      FILTER vplan.asset_key == c._key

      LET adres_json = (c.loc && c.loc.Locatie_puntlocatie && c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres) ? c.loc.Locatie_puntlocatie.DtcPuntlocatie_adres : null
      LET provincie = adres_json && adres_json.DtcAdres_provincie ? adres_json.DtcAdres_provincie : null
      LET gemeente = adres_json && adres_json.DtcAdres_gemeente ? adres_json.DtcAdres_gemeente : null

      LET asset_bestekken = (
        FOR bk IN (c.bs && c.bs.Bestek_bestekkoppeling ? c.bs.Bestek_bestekkoppeling : [])
          FILTER bk != null AND bk._to != null
          LET b = DOCUMENT(bk._to)
          FILTER b != null
          RETURN {
            dossiernummer: b.eDeltaDossiernummer ? b.eDeltaDossiernummer : null,
            besteknummer: b.eDeltaBesteknummer ? b.eDeltaBesteknummer : null,
            aannemer: b.aannemerNaam ? b.aannemerNaam : null
          }
      )
      LET meest_recent_bestek = (LENGTH(asset_bestekken) > 0 ? asset_bestekken[0] : null)

      LET jarenInDienst =
        IS_NULL(vplan.uitDienstDatum)
          ? DATE_DIFF(LEFT(vplan.inDienstDatum, 10), DATE_NOW(), "years")
          : DATE_DIFF(LEFT(vplan.inDienstDatum, 10), LEFT(vplan.uitDienstDatum, 10), "years")
      LET vplan_nummer_kort = vplan.vplan_nummer ? LEFT(vplan.vplan_nummer, 7) : null
      LET tien_jaar_oud = jarenInDienst >= 10

      /* compute geometry and presence flags for dataconflicten logic */
      LET geom = (c.loc && c.loc.Locatie_puntlocatie && c.loc.Locatie_puntlocatie.DtcPuntlocatie_locatie && c.loc.Locatie_puntlocatie.DtcPuntlocatie_locatie.geometry) ? c.loc.Locatie_puntlocatie.DtcPuntlocatie_locatie.geometry : null
      LET vplan_has_id = (HAS(vplan, '_key') && vplan._key != null) || (HAS(vplan, 'uuid') && vplan.uuid != null) || (HAS(vplan, 'vplan_uuid') && vplan.vplan_uuid != null)

      /* Translate SQL CASE logic to AQL booleans: */
      LET dataconflicten = (
        /* WHEN vplan.uuid IS NULL AND v.actief = TRUE AND v.toestand = 'in-gebruik' THEN TRUE */
        ((NOT vplan_has_id) && c.AIMDBStatus_isActief == true && c.toestand == 'in-gebruik')
        /* WHEN vplan.uitdienstdatum IS NULL AND vplan.uuid IS NOT NULL AND v.actief = TRUE AND v.toestand NOT IN ('in-gebruik', 'overgedragen') THEN TRUE */
        || ((vplan.uitDienstDatum == null) && vplan_has_id && c.AIMDBStatus_isActief == true && (c.toestand != 'in-gebruik' && c.toestand != 'overgedragen'))
        /* WHEN (l.adres_provincie IS NULL OR l.geometry IS NULL) AND v.actief = TRUE THEN TRUE */
        || ((provincie == null || geom == null) && c.AIMDBStatus_isActief == true)
      )

      LET base_row = {
        uuid: c._key,
        installatie: (c.naampad ? regex_matches(c.naampad, '^[^/]{1,10}', false)[0] : null),
        naampad: c.naampad,
        actief: c.AIMDBStatus_isActief,
        toestand: c.toestand,
        adres_gemeente: gemeente,
        adres_provincie: provincie,
        indienstdatum: vplan.inDienstDatum,
        uitdienstdatum: vplan.uitDienstDatum,
        vplan_nr: vplan.vplannummer,
        vplan_nr_kort: vplan_nummer_kort,
        commentaar: (vplan.commentaar ? vplan.commentaar : 'onbeschikbaar'),
        edeltadossiernummer: (meest_recent_bestek != null ? meest_recent_bestek.dossiernummer : null),
        aannemernaam: (meest_recent_bestek != null ? meest_recent_bestek.aannemer : null),
        tien_jaar_oud: tien_jaar_oud,
        dataconflicten: dataconflicten
      }

      /* Convert any ARRAY/OBJECT attribute to a JSON string */
      LET safe_pairs = (
        FOR k IN ATTRIBUTES(base_row)
          LET v = base_row[k]
          LET safe_v = (IS_OBJECT(v) OR IS_ARRAY(v) ? JSON_STRINGIFY(v) : v)
          RETURN { k: safe_v }
      )
      RETURN MERGE(safe_pairs)
)

RETURN rows
"""
