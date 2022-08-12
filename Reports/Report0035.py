from DQReport import DQReport


class Report0035:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0035',
                               title="Bestekkoppelingen die bijna vervallen (komende 60 dagen)",
                               spreadsheet_id='1Q0ypijGhIMmax4iR3DHHu4FMYVbkU_LCQhBAyzbIA2k',
                               datasource='PostGIS',
                               persistent_column='')

        self.report.result_query = """
WITH s AS (
	SELECT (NOW() < date(eindDatum) AND date(eindDatum) < (NOW() + INTERVAL '30 DAYS')) AS bijna_verlopen, eindDatum, assetuuid 
	FROM bestekkoppelingen 
		LEFT JOIN assets ON assets.uuid = bestekkoppelingen.assetUuid
	WHERE assets.actief = TRUE AND bestekkoppelingen.koppelingstatus = 'ACTIEF')
SELECT assets.uuid, assets.naampad, assets.actief, assets.toestand, to_char(bestekkoppelingen.startDatum, 'YYYY-MM-DD HH24:MI:SS OF'), TO_CHAR(bestekkoppelingen.eindDatum, 'YYYY-MM-DD HH24:MI:SS OF'), bestekkoppelingen.koppelingstatus, bestekken.eDeltaBesteknummer, bestekken.eDeltaDossiernummer
FROM s 
	LEFT JOIN assets ON s.assetUuid = assets.uuid
	LEFT JOIN bestekkoppelingen ON assets.uuid = bestekkoppelingen.assetUuid
	LEFT JOIN bestekken ON bestekKoppelingen.bestekUuid = bestekken.uuid
WHERE bijna_verlopen = TRUE AND bestekkoppelingen.koppelingstatus IN ('ACTIEF', 'TOEKOMSTIG')
ORDER BY s.eindDatum, naampad, bestekkoppelingen.eindDatum;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
