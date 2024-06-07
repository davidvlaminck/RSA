from DQReport import DQReport


class Report0104:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0104', title='Dubbele EAN nummers over legacy en OTL assets',
                               spreadsheet_id='1yZpc1jcFUwEIMYSC0B4JCLhMtHYAnW0Ua6WYtW_gGew', datasource='PostGIS',
                               persistent_column='G')

        self.report.result_query = """
WITH ean_info AS (
	SELECT DISTINCT assets.uuid, assets.naampad, assets.toestand, at1.uri, ean AS elektrisch_aansluitpunt_ean, aansluiting AS elektrisch_aansluitpunt_aansluiting, 
	a2.waarde AS via_hoort_bij_ean, onderdelen.naam AS via_hoort_bij_naam, onderdelen.uuid as onderdeel_uuid, at2.uri AS onderdeel_type, CASE WHEN forfait.uuid IS NOT NULL THEN 1 ELSE 10 END AS forfait
	FROM assets 
		LEFT JOIN elek_aansluitingen ea ON assets.uuid = ea.assetuuid 
		LEFT JOIN assettypes at1 ON at1.uuid = assets.assettype 
		LEFT JOIN assetrelaties a ON assets.uuid = a.doeluuid AND a.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2' -- HoortBij
		LEFT JOIN assets onderdelen ON a.bronuuid = onderdelen.uuid AND onderdelen.assettype in ('b4ee4ea9-edd1-4093-bce1-d58918aee281', '8e9307e2-4dd6-4a46-a298-dd0bc8b34236') AND onderdelen.actief = TRUE -- DNBLaagspanning & DNBHoogspanning 
		LEFT JOIN assettypes at2 ON at2.uuid = onderdelen.assettype 
		LEFT JOIN attribuutwaarden a2 ON onderdelen.uuid = a2.assetuuid AND a2.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698' -- eanNummer
		LEFT JOIN assetrelaties voedt_rel ON onderdelen.uuid = voedt_rel.bronuuid AND voedt_rel.relatietype = 'f2c5c4a1-0899-4053-b3b3-2d662c717b44' -- Voedt
		LEFT JOIN assets forfait ON voedt_rel.doeluuid = forfait.uuid AND forfait.assettype = 'ffb9a236-fb9e-406f-a602-271b68e62afc' AND forfait.actief = TRUE -- DNBLaagspanning & DNBHoogspanning 
	WHERE (ea.assetuuid IS NOT NULL OR a2.waarde IS NOT NULL)
		AND assets.actief = TRUE),
normalized_ean AS (
	SELECT
		CASE WHEN onderdeel_uuid IS NOT NULL THEN onderdeel_uuid ELSE uuid END AS asset_uuid, 
		CASE WHEN onderdeel_uuid IS NOT NULL THEN onderdeel_type ELSE uri END AS asset_type, 
		CASE WHEN onderdeel_uuid IS NOT NULL THEN via_hoort_bij_naam ELSE naampad END AS asset_naam,
		CASE WHEN onderdeel_uuid IS NOT NULL THEN via_hoort_bij_ean ELSE elektrisch_aansluitpunt_ean END AS ean_nummer, 
		forfait 
	FROM ean_info),
grouped AS (
	SELECT ean_nummer, SUM(forfait) AS ean_score FROM normalized_ean GROUP BY 1)
SELECT normalized_ean.*, toestand
FROM grouped 
	LEFT JOIN normalized_ean ON normalized_ean.ean_nummer = grouped.ean_nummer 
	LEFT JOIN assets ON assets.uuid = asset_uuid
WHERE ean_score > 10
ORDER BY normalized_ean.ean_nummer;
"""

    # assign a score of 1 to every forfaitair and 10 to every non-forfaitair.
    # group by ean_nummer this will give a score of <= 10 for every ean_nummer that is only forfaitair.
    # forfaitair + a regular EAN will give a score of > 10 and will be reported.

    def run_report(self, sender):
        self.report.run_report(sender=sender)
