from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0039(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0039',
                               title="Lichtmast LED",
                               spreadsheet_id='1DZjg3zbcoY7_9Q0qj74KkgLL3eOwWa7e4_0SlbLMM5o',
                               datasource='PostGIS',
                               convert_columns_to_numbers=['K', 'S', 'X', 'Y'],
                               excel_filename='[RSA] Lichtmast LED.xlsx',)

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
	('R0082051',0.160,0.160)
),
cte_attribuutwaarden AS (
    SELECT 
        assetuuid,
        MAX(CASE WHEN attribuutuuid = '6f3d2728-448c-4975-8f4a-cba21d2634b8' THEN waarde END) AS aanstuurstroomDriversInMa,
        MAX(CASE WHEN attribuutuuid = '568ba32e-847c-496a-be20-5d022897f032' THEN waarde END) AS aantal_verlichtingstoestellen,
        MAX(CASE WHEN attribuutuuid = '6e319c32-8e94-476c-965f-32b93c461d20' THEN waarde END) AS contractnummer_levering_LED,
        MAX(CASE WHEN attribuutuuid = 'ed270590-4b11-421d-b921-36034323a9a9' THEN waarde END) AS datum_installatie_LED,
        MAX(CASE WHEN attribuutuuid = '070149cc-55f4-491f-a034-21e832e3a9e5' THEN waarde END) AS lamp_type,
        MAX(CASE WHEN attribuutuuid = 'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b' THEN waarde END) AS LED_verlichting,
        MAX(CASE WHEN attribuutuuid = '218f8269-21eb-445a-9c77-acb3faf6c3ba' THEN waarde END) AS lumen_pakket_LED,
        MAX(CASE WHEN attribuutuuid = '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50' THEN waarde END) AS verlichtingstoestel_systeemvermogen
    FROM attribuutwaarden
    WHERE attribuutuuid IN (
        '6f3d2728-448c-4975-8f4a-cba21d2634b8',
        '568ba32e-847c-496a-be20-5d022897f032',
        '6e319c32-8e94-476c-965f-32b93c461d20',
        'ed270590-4b11-421d-b921-36034323a9a9',
        '070149cc-55f4-491f-a034-21e832e3a9e5',
        'e7ad2d9f-45f3-4e4a-be98-51d71e19c28b',
        '218f8269-21eb-445a-9c77-acb3faf6c3ba',
        '8ea7f7ef-c187-4a68-a92b-6a0ca855ba50'
    )
    GROUP BY assetuuid
),
cte_ruwe_data AS (
    SELECT 
        a.uuid, 
        a.naampad, 
        a.toestand, 
        a.actief,
        COALESCE(l.x, 0) AS x,
        COALESCE(l.y, 0) AS y,
        COALESCE(l.z, 0) AS z,
        l.ident8,
        COALESCE(l.referentiepaal_opschrift, 0) AS referentiepaal_opschrift,
        COALESCE(l.referentiepaal_afstand, 0) AS referentiepaal_afstand,
        l.adres_gemeente,
        CASE WHEN l.adres_provincie = 'Brussel' THEN 'Vlaams-Brabant' ELSE l.adres_provincie END AS adres_provincie,
        l.adres_provincie AS adres_provincie_origineel_met_brussel,
        'POINT Z (' || l.x || ' ' || l.y || ' ' || COALESCE(l.z, 0) || ')' AS wkt_geom
    FROM assets a
    LEFT JOIN locatie l ON a.uuid = l.assetuuid 
    WHERE a.assettype = '4dfad588-277c-480f-8cdc-0889cfaf9c78'
      AND a.actief = TRUE
),
cte_opkuis AS (
    SELECT 
        r.*,
        CASE 
            WHEN aw.aanstuurstroomDriversInMa IS NOT NULL AND aw.lamp_type <> 'LED' THEN 'LED'
            WHEN aw.lumen_pakket_LED IS NOT NULL AND aw.lumen_pakket_LED <> '0' THEN 'LED'
            ELSE aw.lamp_type 
        END AS lamp_type_opgekuist,
        COALESCE(aw.aantal_verlichtingstoestellen::NUMERIC, 1) AS aantal_verlichtingstoestellen_getal,
        aw.*
    FROM cte_ruwe_data r
    LEFT JOIN cte_attribuutwaarden aw ON r.uuid = aw.assetuuid
),
cte_awegen_index AS (
    SELECT aweg_ident8, beginpositie, eindpositie
    FROM cte_awegen
),
cte_opkuis2 AS (
    SELECT 
        o.*,
        CASE 
            WHEN o.lamp_type_opgekuist = 'LED' THEN 'True' 
            WHEN o.LED_verlichting IS NULL THEN 'False'
            ELSE o.LED_verlichting 
        END AS led_verlichting_opgekuist,
        CASE 
            WHEN o.lamp_type_opgekuist = 'LED' THEN 75 
            WHEN o.lamp_type_opgekuist = 'HPIT 250W' then 250
            WHEN o.lamp_type_opgekuist SIMILAR TO '%-(250|70|1000|100|150|140|210|400|600|90|60|50|35|45)%' 
                THEN CAST(REGEXP_REPLACE(o.lamp_type_opgekuist, '[^0-9]', '', 'g') AS INTEGER)
            WHEN o.lamp_type_opgekuist LIKE 'NaLP131%' THEN 131
            WHEN o.lamp_type_opgekuist LIKE 'NaLP180%' THEN 180
            WHEN o.lamp_type_opgekuist IN ('NaLP36','TL 36W') THEN 36
            WHEN o.lamp_type_opgekuist = 'NaLP66' THEN 66
            WHEN o.lamp_type_opgekuist = 'NaLP91' THEN 91
            ELSE 0 
        END AS vermogen
    FROM cte_opkuis o
),
cte_met_wegen AS (
    SELECT 
        o.*,
        aw.aweg_ident8
    FROM cte_opkuis2 o
    LEFT JOIN cte_awegen_index aw 
        ON o.ident8 = aw.aweg_ident8 
        AND (o.referentiepaal_opschrift + o.referentiepaal_afstand / 1000.0) BETWEEN aw.beginpositie AND aw.eindpositie
)
SELECT 
    *, 
    CASE 
        WHEN lamp_type_opgekuist = 'LED' THEN vermogen 
        ELSE vermogen * 1.15 
    END AS vermogen_inc_verlies,
    CASE 
        WHEN ident8 LIKE 'A%' THEN 'A-Weg' 
        WHEN ident8 LIKE 'N%' THEN 'N-Weg' 
        WHEN aweg_ident8 IS NOT NULL THEN 'A-Weg'
        WHEN wkt_geom IS NOT NULL THEN 'Gemeente-Weg'
        ELSE 'locatie ongekend'
    END AS wegcategorie
FROM cte_met_wegen
"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
