from DQReport import DQReport


class Report0016:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0016',
                               title='Netwerkpoorten hebben een Bevestiging relatie met een Netwerkelement of een Netwerkkaart',
                               spreadsheet_id='16NJCwhrHnYuz6Z9leqGswfOR0bt7EdBK_GonPB-3y7o',
                               datasource='PostGIS',
                               persistent_column='C')
        self.report.result_query = """
WITH poorten AS (
	SELECT * 
	FROM assets 
	WHERE assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' AND actief = TRUE), -- Netwerkpoort
relaties AS (
	SELECT assetrelaties.uuid, 
		CASE WHEN bron.uuid IS NOT NULL THEN doeluuid
			WHEN doel.uuid IS NOT NULL THEN bronuuid
			ELSE NULL END AS bron_uuid 
	FROM assetrelaties
		LEFT JOIN assets bron ON assetrelaties.bronuuid = bron.uuid AND bron.actief = TRUE AND bron.assettype IN ('b6f86b8d-543d-4525-8458-36b498333416', '0809230e-ebfe-4802-94a4-b08add344328') -- Netwerkelement/Netwerkkaart
		LEFT JOIN assets doel ON assetrelaties.doeluuid = doel.uuid AND doel.actief = TRUE AND doel.assettype IN ('b6f86b8d-543d-4525-8458-36b498333416', '0809230e-ebfe-4802-94a4-b08add344328') -- Netwerkelement/Netwerkkaart
	WHERE relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20' -- Bevestiging
		AND (bron.uuid IS NOT NULL OR doel.uuid IS NOT NULL))
SELECT poorten.uuid, poorten.naam 
FROM poorten
	LEFT JOIN relaties ON poorten.uuid = relaties.bron_uuid
WHERE relaties.uuid IS NULL;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
