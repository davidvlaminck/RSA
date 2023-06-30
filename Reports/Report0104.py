from DQReport import DQReport


class Report0104:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0104', title='Dubbele EAN nummers over legacy en OTL assets',
                               spreadsheet_id='1yZpc1jcFUwEIMYSC0B4JCLhMtHYAnW0Ua6WYtW_gGew', datasource='PostGIS',
                               persistent_column='F')

        self.report.result_query = """
WITH ean_info AS (
	SELECT DISTINCT assets.uuid, assets.naampad, assets.toestand, at1.uri, ean AS elektrisch_aansluitpunt_ean, aansluiting AS elektrisch_aansluitpunt_aansluiting, 
	a2.waarde AS via_hoort_bij_ean, onderdelen.naam AS via_hoort_bij_naam, onderdelen.uuid as onderdeel_uuid, at2.uri AS onderdeel_type
	FROM assets 
		LEFT JOIN elek_aansluitingen ea ON assets.uuid = ea.assetuuid 
		LEFT JOIN assettypes at1 ON at1.uuid = assets.assettype 
		LEFT JOIN assetrelaties a ON assets.uuid = a.doeluuid AND a.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2' -- HoortBij
		LEFT JOIN assets onderdelen ON a.bronuuid = onderdelen.uuid AND onderdelen.assettype in ('b4ee4ea9-edd1-4093-bce1-d58918aee281', '8e9307e2-4dd6-4a46-a298-dd0bc8b34236') AND onderdelen.actief = TRUE -- DNBLaagspanning & DNBHoogspanning 
		LEFT JOIN assettypes at2 ON at2.uuid = onderdelen.assettype 
		LEFT JOIN attribuutwaarden a2 ON onderdelen.uuid = a2.assetuuid AND a2.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698' -- eanNummer
	WHERE (ea.assetuuid IS NOT NULL OR a2.waarde IS NOT NULL)
		AND assets.actief = TRUE),
normalized_ean AS (
	SELECT
		CASE WHEN onderdeel_uuid IS NOT NULL THEN onderdeel_uuid ELSE uuid END AS asset_uuid, 
		CASE WHEN onderdeel_uuid IS NOT NULL THEN onderdeel_type ELSE uri END AS asset_type, 
		CASE WHEN onderdeel_uuid IS NOT NULL THEN via_hoort_bij_naam ELSE naampad END AS asset_naam,
		CASE WHEN onderdeel_uuid IS NOT NULL THEN via_hoort_bij_ean ELSE elektrisch_aansluitpunt_ean END AS ean_nummer
	FROM ean_info),
grouped AS (
	SELECT ean_nummer, count(*) AS ean_aantal FROM normalized_ean GROUP BY 1)
SELECT normalized_ean.*, toestand
FROM grouped 
	LEFT JOIN normalized_ean ON normalized_ean.ean_nummer = grouped.ean_nummer 
	LEFT JOIN assets ON assets.uuid = asset_uuid
WHERE ean_aantal > 1
ORDER BY normalized_ean.ean_nummer;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
