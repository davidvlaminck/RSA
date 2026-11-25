from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0035(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0035',
                               title="Bestekkoppelingen die bijna vervallen (komende 30 dagen)",
                               spreadsheet_id='1DfUOm6Z38BYR7R809wiUDNrd8Fj4O-dC59ylHn99iqE',
                               datasource='PostGIS',
                               persistent_column='J',
                               excel_filename='[RSA] Bestekkoppelingen die bijna vervallen (komende 30 dagen).xlsx',)

        self.report.result_query = """
WITH s AS (
	SELECT (NOW() < date(eindDatum) AND date(eindDatum) < (NOW() + INTERVAL '30 DAYS')) AS bijna_verlopen, eindDatum, assetuuid 
	FROM bestekkoppelingen 
		LEFT JOIN assets ON assets.uuid = bestekkoppelingen.assetUuid
	WHERE assets.actief = TRUE AND lower(bestekkoppelingen.koppelingstatus) = 'actief')
SELECT assets.uuid, assets.naampad, assets.actief, assets.toestand, to_char(bestekkoppelingen.startDatum, 'YYYY-MM-DD HH24:MI:SS OF') AS startDatum, TO_CHAR(bestekkoppelingen.eindDatum, 'YYYY-MM-DD HH24:MI:SS OF') AS einddatum, bestekkoppelingen.koppelingstatus, bestekken.eDeltaBesteknummer, bestekken.eDeltaDossiernummer
FROM s 
	LEFT JOIN assets ON s.assetUuid = assets.uuid
	LEFT JOIN bestekkoppelingen ON assets.uuid = bestekkoppelingen.assetUuid
	LEFT JOIN bestekken ON bestekKoppelingen.bestekUuid = bestekken.uuid
WHERE bijna_verlopen = TRUE AND lower(bestekkoppelingen.koppelingstatus) IN ('actief', 'toekomstig')
ORDER BY s.eindDatum, naampad, bestekkoppelingen.eindDatum;"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)

aql_query = """
LET now   = DATE_NOW()
LET upper = now + 30 * 24 * 60 * 60 * 1000 /* 30 days in ms */

FOR bk IN bestekkoppelingen
  // Test unhappy flow
  // FILTER bk._from == 'assets/6bb91264-d171-4304-9154-6c1b97a8c7fe'
  // Test happy flow
  FILTER bk._from == 'assets/6bba9ecc-2c56-4225-aaec-e0241d0e7f75'
  
  // most performant = substring(), most stable = split()
   LET status = SPLIT(bk.DtcBestekkoppeling_status, '/')[-1]
  // LET status = SUBSTRING(bk.DtcBestekkoppeling_status, 69)
  FILTER status IN ["actief", "toekomstig"]

  // uncomment after bugfix bk.status
  // FILTER bk.status In ["actief", "toekomstig"]

  LET asset = DOCUMENT(bk._from)
  FILTER asset != null AND asset.AIMDBStatus_isActief == true

  LET start_ts = bk.DtcBestekkoppeling_actiefVan ? DATE_TIMESTAMP(bk.DtcBestekkoppeling_actiefVan) : null
  LET eind_ts  = bk.DtcBestekkoppeling_actiefTot  ? DATE_TIMESTAMP(bk.DtcBestekkoppeling_actiefTot)  : null

  // Group per asset (only the fields we actually need are carried)
  COLLECT bk_from = bk._from INTO group

  // Null-first, then ascending; keep only the first element
  LET chosen = FIRST(FOR g IN group SORT g.eind_ts ASC RETURN g)

  // Post-aggregation filter
  FILTER chosen.eind_ts != null AND chosen.eind_ts > now AND chosen.eind_ts < upper

  // Reuse already-loaded asset; fetch bestek only for the chosen record
  LET asset  = chosen.asset
  LET bestek = chosen.bk._to ? DOCUMENT(chosen.bk._to) : null

  LET start_ts_formatted = chosen.start_ts ? DATE_FORMAT(chosen.start_ts, "%d-%m-%y") : null
  LET eind_ts_formatted  = chosen.eind_ts  ? DATE_FORMAT(chosen.eind_ts,  "%d-%m-%y") : null

  SORT asset.NaampadObject_naampad

  RETURN {
    uuid: asset._key,
    naampad: asset.NaampadObject_naampad,
    actief: asset.AIMDBStatus_isActief,
    toestand: asset.toestand,
    bestekkoppeling_start_datum: start_ts_formatted,
    bestekkoppeling_eind_datum: eind_ts_formatted,
    bestekkoppeling_status: chosen.status,
    bestek_eDeltaBesteknummer: bestek ? bestek.eDeltaBesteknummer : null,
    bestek_eDeltaDossiernummer: bestek ? bestek.eDeltaDossiernummer : null
  }
  """