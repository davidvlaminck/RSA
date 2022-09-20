from DQReport import DQReport


class Report0039:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0039',
                               title="Lichtmast LED",
                               spreadsheet_id='1DZjg3zbcoY7_9Q0qj74KkgLL3eOwWa7e4_0SlbLMM5o',
                               datasource='PostGIS')

        self.report.result_query = """
WITH ruwe_data AS (
	SELECT assets.uuid, assets.naampad, assets.toestand, assets.actief
		, attribuutwaarden_aanstuurstroomDriversInMa.waarde AS aanstuurstroomDriversInMa
		, attribuutwaarden_aantal_verlichtingstoestellen.waarde AS aantal_verlichtingstoestellen
		, attribuutwaarden_contractnummer_levering_LED.waarde AS contractnummer_levering_LED
		, attribuutwaarden_datum_installatie_LED.waarde AS datum_installatie_LED
		, attribuutwaarden_lamp_type.waarde AS lamp_type
		, attribuutwaarden_LED_verlichting.waarde AS LED_verlichting
		, attribuutwaarden_lumen_pakket_LED.waarde AS lumen_pakket_LED
		-- , attribuutwaarden_verlichtingstoestel_systeemvermogen.waarde AS verlichtingstoestel_systeemvermogen
		, locatie.adres_gemeente , locatie.adres_provincie 
	FROM assets 
		LEFT JOIN attribuutwaarden attribuutwaarden_aanstuurstroomDriversInMa ON assets.uuid = attribuutwaarden_aanstuurstroomDriversInMa.assetuuid AND attribuutwaarden_aanstuurstroomDriversInMa.attribuutuuid = '6f3d2728-448c-4975-8f4a-cba21d2634b8'
		LEFT JOIN attribuutwaarden attribuutwaarden_aantal_verlichtingstoestellen ON assets.uuid = attribuutwaarden_aantal_verlichtingstoestellen.assetuuid AND attribuutwaarden_aantal_verlichtingstoestellen.attribuutuuid = '568ba32e-847c-496a-be20-5d022897f032'
		LEFT JOIN attribuutwaarden attribuutwaarden_contractnummer_levering_LED ON assets.uuid = attribuutwaarden_contractnummer_levering_LED.assetuuid AND attribuutwaarden_contractnummer_levering_LED.attribuutuuid = '6e319c32-8e94-476c-965f-32b93c461d20'
		LEFT JOIN attribuutwaarden attribuutwaarden_datum_installatie_LED ON assets.uuid = attribuutwaarden_datum_installatie_LED.assetuuid AND attribuutwaarden_datum_installatie_LED.attribuutuuid = 'ed270590-4b11-421d-b921-36034323a9a9'
		LEFT JOIN attribuutwaarden attribuutwaarden_lamp_type ON assets.uuid = attribuutwaarden_lamp_type.assetuuid AND attribuutwaarden_lamp_type.attribuutuuid = '070149cc-55f4-491f-a034-21e832e3a9e5'
		LEFT JOIN attribuutwaarden attribuutwaarden_LED_verlichting ON assets.uuid = attribuutwaarden_LED_verlichting.assetuuid AND attribuutwaarden_LED_verlichting.attribuutuuid = 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b'
		LEFT JOIN attribuutwaarden attribuutwaarden_lumen_pakket_LED ON assets.uuid = attribuutwaarden_lumen_pakket_LED.assetuuid AND attribuutwaarden_lumen_pakket_LED.attribuutuuid = '218f8269-21eb-445a-9c77-acb3faf6c3ba'
		-- LEFT JOIN attribuutwaarden attribuutwaarden_verlichtingstoestel_systeemvermogen ON assets.uuid = attribuutwaarden_verlichtingstoestel_systeemvermogen.assetuuid AND attribuutwaarden_verlichtingstoestel_systeemvermogen.attribuutuuid = '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50'
		LEFT JOIN locatie ON assets.uuid = locatie.assetuuid 
	WHERE assettype = '4dfad588-277c-480f-8cdc-0889cfaf9c78' AND assets.actief = TRUE),
opkuis1 AS (
	SELECT *, 
		CASE WHEN aanstuurstroomDriversInMa IS NOT NULL AND lamp_type <> 'LED' THEN 'LED'
			WHEN lumen_pakket_LED IS NOT NULL AND lumen_pakket_LED <> '0' THEN 'LED'
			ELSE lamp_type END AS lamp_type_opgekuist,
		CASE WHEN aantal_verlichtingstoestellen IS NOT NULL THEN aantal_verlichtingstoestellen::NUMERIC
			ELSE 1 END AS aantal_verlichtingstoestellen_getal
	FROM ruwe_data),
opkuis2 AS (
	SELECT *, 
		CASE WHEN lamp_type_opgekuist = 'LED' THEN 'True' 
			WHEN led_verlichting IS NULL THEN 'False'
			ELSE led_verlichting END AS led_verlichting_opgekuist,
		CASE WHEN lamp_type_opgekuist = 'LED' THEN 75 
			WHEN lamp_type_opgekuist = 'HPIT 250W' OR lamp_type_opgekuist LIKE '%-250%' THEN 250
			WHEN lamp_type_opgekuist LIKE '%-70%' THEN 70
			WHEN lamp_type_opgekuist LIKE '%-1000%' THEN 1000
			WHEN lamp_type_opgekuist LIKE '%-100%' THEN 100
			WHEN lamp_type_opgekuist LIKE '%-150%' THEN 150
			WHEN lamp_type_opgekuist LIKE '%-140%' THEN 140
			WHEN lamp_type_opgekuist LIKE '%-210%' THEN 210
			WHEN lamp_type_opgekuist LIKE '%-400%' THEN 400
			WHEN lamp_type_opgekuist LIKE '%-600%' THEN 600
			WHEN lamp_type_opgekuist LIKE '%-90%' THEN 90
			WHEN lamp_type_opgekuist LIKE '%-60%' THEN 60
			WHEN lamp_type_opgekuist LIKE '%-50%' THEN 50
			WHEN lamp_type_opgekuist LIKE '%-35%' THEN 35
			WHEN lamp_type_opgekuist LIKE '%-45%' THEN 45
			WHEN lamp_type_opgekuist LIKE 'NaLP131%' THEN 131
			WHEN lamp_type_opgekuist LIKE 'NaLP180%' THEN 180
			WHEN lamp_type_opgekuist IN ('NaLP36','TL 36W') THEN 36
			WHEN lamp_type_opgekuist = 'NaLP66' THEN 66
			WHEN lamp_type_opgekuist = 'NaLP91' THEN 91
		ELSE 0 END AS vermogen
	FROM opkuis1),
-- SELECT DISTINCT lamp_type_opgekuist, vermogen FROM opkuis2; -- mappingtabel vermogens
opkuis3 AS (
	SELECT *, 
		CASE WHEN lamp_type_opgekuist = 'LED' THEN vermogen ELSE vermogen*1.15 END AS vermogen_inc_verlies,
		CASE WHEN lamp_type_opgekuist LIKE 'NaHP%' THEN 'NAHP' 
			WHEN lamp_type_opgekuist LIKE 'NaLP%' THEN 'NALP'
			WHEN lamp_type_opgekuist LIKE 'MHHP%' THEN 'MHHP'
			WHEN lamp_type_opgekuist LIKE 'HPIT%' OR lamp_type_opgekuist LIKE 'TL%' THEN 'andere'
			WHEN lamp_type_opgekuist IS NULL THEN 'niet gekend'
			ELSE lamp_type_opgekuist END AS beperkte_benaming 
	FROM opkuis2)
-- SELECT DISTINCT lamp_type_opgekuist, beperkte_benaming FROM opkuis3; -- mappingtabel beperkte_benaming
SELECT * FROM opkuis3;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
