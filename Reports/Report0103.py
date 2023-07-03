from DQReport import DQReport


class Report0103:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0103', title='Inconsistente EAN nummers tusen legacy en OTL',
                               spreadsheet_id='1o1Z2zDeSn4pUotSBczST4cZRpzxg1-2Ef6vrRuNyjoA', datasource='PostGIS',
                               persistent_column='K', link_type='eminfra')

        self.report.result_query = """
WITH ean_info AS (
    SELECT DISTINCT assets.uuid, assets.naampad, assets.toestand, at1.uri,  ean AS elektrisch_aansluitpunt_ean, aansluiting AS elektrisch_aansluitpunt_aansluiting, a2.waarde AS via_hoort_bij_ean	, onderdelen.naam AS via_hoort_bij_naam, onderdelen.uuid as onderdeel_uuid, at2.uri AS onderdeel_type
    FROM assets 
        LEFT JOIN elek_aansluitingen ea ON assets.uuid = ea.assetuuid 
        INNER JOIN assettypes at1 ON at1.uuid = assets.assettype 
        LEFT JOIN assetrelaties a ON assets.uuid = a.doeluuid AND a.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2' -- HoortBij
        LEFT JOIN assets onderdelen ON a.bronuuid = onderdelen.uuid AND onderdelen.assettype in ('b4ee4ea9-edd1-4093-bce1-d58918aee281', '8e9307e2-4dd6-4a46-a298-dd0bc8b34236') and onderdelen.actief = TRUE -- DNBLaagspanning & DNBHoogspanning
        LEFT JOIN assettypes at2 ON at2.uuid = onderdelen.assettype 
        LEFT JOIN attribuutwaarden a2 ON onderdelen.uuid = a2.assetuuid AND a2.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698' -- eanNummer
    WHERE (ea.assetuuid IS NOT NULL OR a2.waarde IS NOT NULL)
        AND assets.actief = TRUE AND a2.waarde <> ean)
SELECT * FROM ean_info;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
