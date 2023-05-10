from DQReport import DQReport


class Report0083:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0084',
                               title='Verkeersregelaars hebben een vplannummer en vplandatum dat overeenkomt met het legacy vplan',
                               spreadsheet_id='1pGZUOMXLeWRo0Ykzshxt9PJN2tCbznsBxQf0mgh7Zos',
                               datasource='PostGIS',
                               persistent_column='H')

        self.report.result_query = """
WITH vrs AS (
	SELECT assets.*, vplandatum.waarde::timestamptz AS vplandatum, vplannummer.waarde AS vplannummer 
	FROM assets 
		LEFT JOIN attribuutwaarden vplandatum ON vplandatum.assetuuid = assets.uuid AND vplandatum.attribuutuuid = 'c8f6b633-efba-4124-838b-805ae9a82c5a'
		LEFT JOIN attribuutwaarden vplannummer ON vplannummer.assetuuid = assets.uuid AND vplannummer.attribuutuuid = 'b943728d-d69d-4425-a4eb-db50989d9923'
	WHERE actief = TRUE AND assettype = '3d24792a-6941-481b-9c8c-739309fd3ffb'),
vr_legacy AS (SELECT * FROM assets WHERE actief = TRUE AND assettype = '13fa9473-f919-432a-bd00-bc19645bd30a'),
recentste_koppeling AS (
	SELECT vr_legacy.uuid, max(indienstdatum) AS max_indienstdatum 
	FROM vr_legacy 
		LEFT JOIN vplan_koppelingen ON vplan_koppelingen.assetuuid = vr_legacy.uuid 
	WHERE uitdienstdatum IS NULL
	GROUP BY 1),
vr_legacy_met_koppeling AS (
	SELECT vr_legacy.*, vplan_koppelingen.indienstdatum, vplan_koppelingen.vplannummer 
	FROM vr_legacy 
		LEFT JOIN recentste_koppeling ON vr_legacy.uuid = recentste_koppeling.uuid
		LEFT JOIN vplan_koppelingen ON vplan_koppelingen.assetuuid = vr_legacy.uuid AND vplan_koppelingen.indienstdatum = recentste_koppeling.max_indienstdatum AND uitdienstdatum IS NULL)
SELECT vrs.uuid, vrs.naam, vrs.vplannummer, vrs.vplandatum, vr_legacy_met_koppeling.uuid AS vrlegacy_uuid, vr_legacy_met_koppeling.indienstdatum AS vrlegacy_vplandatum, vr_legacy_met_koppeling.vplannummer AS  vrlegacy_vplannummer
FROM vrs 
	LEFT JOIN assetrelaties a ON vrs.uuid = a.bronuuid AND a.relatietype  = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
	LEFT JOIN vr_legacy_met_koppeling ON a.doeluuid = vr_legacy_met_koppeling.uuid
WHERE vrs.vplandatum IS NULL OR vrs.vplannummer IS NULL OR (vplandatum <> vr_legacy_met_koppeling.indienstdatum) OR vrs.vplannummer <> vr_legacy_met_koppeling.vplannummer"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
