from DQReport import DQReport


class Report0039:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0039',
                               title="Lichtmast LED",
                               spreadsheet_id='1DZjg3zbcoY7_9Q0qj74KkgLL3eOwWa7e4_0SlbLMM5o',
                               datasource='PostGIS',
                               convert_columns_to_numbers=['K', 'S', 'X', 'Y'])

        self.report.result_query = """
WITH cte_awegen ("aweg_ident8", "beginpositie", "eindpositie") AS ( VALUES
	('B1010001',0.000,5.000),
	('B1010002',0.000,5.000),
	('B4010001',0.000,2.338),
	('B4010002',0.000,2.364),
	('B403001',0.0000,99.9999),
	('B403002',0.0000,99.9999),
	('R0000001',23.634,75.374),
	('R0000002',24.402,75.332),
	('R0001811',0.521,0.521),
	('R0001821',0.000,0.194),
	('R0001841',0.000,0.834),
	('R0001861',0.000,0.451),
	('R0001871',0.000,0.202),
	('R0002241',0.000,0.981),
	('R0002271',0.000,0.672),
	('R0010001',0.000,16.285),
	('R0010002',0.000,15.961),
	('R0020001',78.666,88.698),
	('R0020002',78.441,89.485),
	('R0022211',0.955,0.955),
	('R0022281',0.000,1.171),
	('R0040001',14.927,29.195),
	('R0040002',14.911,28.860),
	('R0040911',0.000,1.517),
	('R0040961',0.338,0.835),
	('R0040981',0.395,0.437),
	('R0080001',4.372,6.372),
	('R0080002',5.809,15.331),
	('R0080911',0.000,0.197),
	('R0080961',0.000,0.212),
	('R0082021',0.000,0.000),
	('R0082051',0.160,0.160)),
cte_attribuutwaarden as (
	select
		assetuuid
		, MAX(CASE WHEN attribuutuuid = '6e319c32-8e94-476c-965f-32b93c461d20' THEN waarde END) AS aanstuurstroomDriversInMa
		, MAX(CASE WHEN attribuutuuid = '568ba32e-847c-496a-be20-5d022897f032' THEN waarde END) AS aantal_verlichtingstoestellen
		, MAX(CASE WHEN attribuutuuid = '6e319c32-8e94-476c-965f-32b93c461d20' THEN waarde END) AS contractnummer_levering_LED
		, MAX(CASE WHEN attribuutuuid = 'ed270590-4b11-421d-b921-36034323a9a9' THEN waarde END) AS datum_installatie_LED
		, MAX(CASE WHEN attribuutuuid = '070149cc-55f4-491f-a034-21e832e3a9e5' THEN waarde END) AS lamp_type
		, MAX(CASE WHEN attribuutuuid = 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b' THEN waarde END) AS LED_verlichting
		, MAX(CASE WHEN attribuutuuid = '218f8269-21eb-445a-9c77-acb3faf6c3ba' THEN waarde END) AS lumen_pakket_LED
		, MAX(CASE WHEN attribuutuuid = '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50' THEN waarde END) AS verlichtingstoestel_systeemvermogen
	from attribuutwaarden
	where attribuutuuid in 
		(
			  '6f3d2728-448c-4975-8f4a-cba21d2634b8'  -- aanstuurstroomDriversInMa
			, '568ba32e-847c-496a-be20-5d022897f032'  -- aantal_verlichtingstoestellen
			, '6e319c32-8e94-476c-965f-32b93c461d20'  -- contractnummer_levering_LED
			, 'ed270590-4b11-421d-b921-36034323a9a9'  -- datum_installatie_LED
			, '070149cc-55f4-491f-a034-21e832e3a9e5'  -- lamp_type
			, 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b'  -- LED_verlichting
			, '218f8269-21eb-445a-9c77-acb3faf6c3ba'  -- lumen_pakket_LED
			, '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50'  -- verlichtingstoestel_systeemvermogen
		)
	group by assetuuid
),
cte_ruwe_data AS (
	SELECT assets.uuid, assets.naampad, assets.toestand, assets.actief
		, aw.aanstuurstroomDriversInMa
		, aw.aantal_verlichtingstoestellen
		, aw.contractnummer_levering_LED
		, aw.datum_installatie_LED
		, aw.lamp_type
		, aw.LED_verlichting
		, aw.lumen_pakket_LED
--		, aw.verlichtingstoestel_systeemvermogen
		, locatie.ident8
		, CASE WHEN referentiepaal_opschrift IS NOT NULL THEN
			CASE WHEN referentiepaal_afstand IS NULL THEN referentiepaal_opschrift
			ELSE referentiepaal_opschrift + referentiepaal_afstand / 1000.0 END
		ELSE NULL END AS locatie_referentiepunt
		, 'POINT Z (' || locatie.x || ' ' || locatie.y || ' ' || coalesce(locatie.z, 0) || ')' as wkt_geom
		, locatie.adres_gemeente
		-- Overschrijf Brussel >> Vlaams-Brabant
		, case 
			when locatie.adres_provincie = 'Brussel' then 'Vlaams-Brabant'
			else locatie.adres_provincie 
		end as adres_provincie
		, locatie.adres_provincie as adres_provincie_origineel_met_brussel
	FROM assets 
		LEFT JOIN cte_attribuutwaarden aw ON assets.uuid = aw.assetuuid
		LEFT JOIN locatie ON assets.uuid = locatie.assetuuid 
	where
		assettype = '4dfad588-277c-480f-8cdc-0889cfaf9c78'
		AND assets.actief = true
	),
opkuis1 AS (
	select
		cte_ruwe_data.*,
		CASE WHEN aanstuurstroomDriversInMa IS NOT NULL AND lamp_type <> 'LED' THEN 'LED'
			WHEN lumen_pakket_LED IS NOT NULL AND lumen_pakket_LED <> '0' THEN 'LED'
			ELSE lamp_type END AS lamp_type_opgekuist,
		CASE WHEN aantal_verlichtingstoestellen IS NOT NULL THEN aantal_verlichtingstoestellen::NUMERIC
			ELSE 1::NUMERIC END AS aantal_verlichtingstoestellen_getal,
		cte_awegen.*		
	FROM cte_ruwe_data
	LEFT JOIN cte_awegen ON ident8 = cte_awegen.aweg_ident8 AND locatie_referentiepunt between cte_awegen.beginpositie AND cte_awegen.eindpositie
),
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
	FROM opkuis1
	),
opkuis3 AS (
	SELECT *, 
		CASE WHEN lamp_type_opgekuist = 'LED' THEN vermogen ELSE vermogen*1.15 END AS vermogen_inc_verlies,
		CASE WHEN lamp_type_opgekuist LIKE 'NaHP%' THEN 'NAHP' 
			WHEN lamp_type_opgekuist LIKE 'NaLP%' THEN 'NALP'
			WHEN lamp_type_opgekuist LIKE 'MHHP%' THEN 'MHHP'
			WHEN lamp_type_opgekuist LIKE 'HPIT%' OR lamp_type_opgekuist LIKE 'TL%' THEN 'andere'
			WHEN lamp_type_opgekuist IS NULL THEN 'niet gekend'
			ELSE lamp_type_opgekuist END AS beperkte_benaming,
		CASE
			WHEN opkuis2.ident8 LIKE 'A%' THEN 'A-Weg'
			WHEN opkuis2.ident8 LIKE 'N%' THEN 'N-Weg'
			WHEN opkuis2.ident8 LIKE 'T%' THEN 'N-Weg'
			WHEN opkuis2.aweg_ident8 IS NOT NULL THEN 'A-Weg'
			WHEN opkuis2.wkt_geom is not null then 'Gemeente-Weg'
			ELSE 'locatie ongekend'
		END AS wegcategorie
	FROM opkuis2)
SELECT * FROM opkuis3;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
