from lib.reports.DQReport import DQReport


class Report0035:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0035',
                               title="Bestekkoppelingen die bijna vervallen (komende 30 dagen)",
                               spreadsheet_id='1DfUOm6Z38BYR7R809wiUDNrd8Fj4O-dC59ylHn99iqE',
                               datasource='PostGIS',
                               persistent_column='J')

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

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET now = DATE_NOW()
LET upper = now + 30 * 24 * 60 * 60 * 1000 /* 30 days in milliseconds */

FOR bk IN bestekkoppelingen
  LET status = SUBSTRING(bk.DtcBestekkoppeling_status, 69)
  FILTER status IN ["actief", "toekomstig"]

  LET start_ts = bk.DtcBestekkoppeling_actiefVan ? DATE_TIMESTAMP(bk.DtcBestekkoppeling_actiefVan) : null  
  LET eind_ts = bk.DtcBestekkoppeling_actiefTot ? DATE_TIMESTAMP(bk.DtcBestekkoppeling_actiefTot) : null
  
  FILTER eind_ts != null and (eind_ts > now AND eind_ts < upper)

  LET start_ts_formatted = start_ts ? DATE_FORMAT(start_ts, "%d-%m-%y") : null
  LET eind_ts_formatted = eind_ts ? DATE_FORMAT(eind_ts, "%d-%m-%y"): null

  LET asset = bk._from ? DOCUMENT(bk._from) : null
  FILTER asset != null AND asset.AIMDBStatus_isActief == true
  
  LET bestek = bk._to ? DOCUMENT(bk._to) : null

SORT eind_ts asc, asset.NaampadObject_naampad

RETURN {
  uuid: asset._key,
  naampad: asset.NaampadObject_naampad,
  actief: asset.AIMDBStatus_isActief,
  toestand: asset.toestand,
  bestekkoppeling_start_datum: start_ts_formatted,
  bestekkoppeling_eind_datum: eind_ts_formatted,
  bestekkoppeling_status: status,
  bestek_uuid: bestek.uuid,
  bestek_eDeltaBesteknummer: bestek ? bestek.eDeltaBesteknummer : null,
  bestek_eDeltaDossiernummer: bestek ? bestek.eDeltaDossiernummer : null
}
"""