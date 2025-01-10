from DQReport import DQReport


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




# WITH actieve_koppelingen AS (
# 	SELECT assetUuid, sum(CASE WHEN lower(koppelingstatus)  IN ('actief', 'toekomstig') THEN 1 ELSE 0 END) AS aantal
# 	FROM bestekkoppelingen
# 	GROUP BY assetUuid),
# s AS (
# 	SELECT ((NOW()- INTERVAL '30 DAYS') < date(eindDatum) AND date(eindDatum) < NOW()) AS reeds_verlopen, eindDatum,
# 	bestekkoppelingen.assetUuid
# 	FROM bestekkoppelingen
# 		LEFT JOIN assets ON assets.uuid = bestekkoppelingen.assetUuid
# 		LEFT JOIN actieve_koppelingen ON assets.uuid = actieve_koppelingen.assetUuid
# 	WHERE assets.actief = TRUE AND actieve_koppelingen.aantal = 0)
# SELECT assets.uuid, assets.naampad, assets.actief, assets.toestand, TO_CHAR(bestekkoppelingen.startDatum, 'YYYY-MM-DD HH24:MI:SS OF') AS startDatum, TO_CHAR(bestekkoppelingen.eindDatum, 'YYYY-MM-DD HH24:MI:SS OF') AS eindDatum, bestekkoppelingen.koppelingstatus, bestekken.eDeltaBesteknummer, bestekken.eDeltaDossiernummer
# FROM s
# 	LEFT JOIN assets ON s.assetUuid = assets.uuid
# 	LEFT JOIN bestekkoppelingen ON assets.uuid = bestekkoppelingen.assetUuid
# 	LEFT JOIN bestekken ON bestekKoppelingen.bestekUuid = bestekken.uuid
# WHERE reeds_verlopen = TRUE
# ORDER BY s.eindDatum DESC, naampad, bestekkoppelingen.eindDatum;
