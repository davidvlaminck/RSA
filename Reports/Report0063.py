from DQReport import DQReport
from LegacyReport import LegacyReport


class Report0063:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = LegacyReport(name='report0063',
                                   title="Overzicht invulgraad installaties per toezichtgroep",
                                   spreadsheet_id='1i-CB_Kox651c9zP8e1Q_XtflOqvta-xlCfKSj7h_4gM',
                                   datasource='PostGIS',
                                   sheet_name='Gegevens',
                                   frequency=7)

        self.report.result_query = """
WITH totaal AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
	WHERE assets.actief = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1 ), 
metKenmerkBestek AS (
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal met bestek' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
	WHERE assets.actief = TRUE AND assettypes.bestek = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
bestek_koppelingen AS ( 
	SELECT DISTINCT assetUuid
	FROM bestekkoppelingen
	WHERE koppelingStatus = 'ACTIEF'), 
metBestek AS (
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Met bestek' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN bestek_koppelingen ON assets.uuid = bestek_koppelingen.assetUuid
	WHERE assets.actief = TRUE AND assettypes.bestek = TRUE AND bestek_koppelingen.assetUuid IS NOT NULL AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
metKenmerkLocatie AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal met GPS' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
	WHERE assets.actief = TRUE AND assettypes.locatie = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1 ), 
metLocatie AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Met GPS' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN locatie ON assets.uuid = locatie.assetuuid 
	WHERE assets.actief = TRUE AND locatie.x IS NOT NULL AND locatie.x <> 0 AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1 ), 
metKenmerkBeheerder AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal met beheerder' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
	WHERE assets.actief = TRUE AND assettypes.beheerder = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
metBeheerder AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Met beheerder' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN beheerders ON assets.schadebeheerder = beheerders.uuid
	WHERE assets.actief = TRUE AND beheerders.referentie IS NOT NULL AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
metKenmerkToezicht AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
		CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal met toezichter' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
	WHERE assets.actief = TRUE
		AND assettypes.toezicht = TRUE
		AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
metToezichter AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Met toezichter' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN identiteiten ON assets.toezichter = identiteiten.uuid
	WHERE assets.actief = TRUE AND identiteiten.gebruikersnaam IS NOT NULL AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
	GROUP BY 1), 
metKenmerkGevoedGoor AS ( 
	SELECT CASE
		WHEN toezichtgroepen.referentie IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Totaal met voedingsbron' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		WHERE assets.actief = TRUE AND assettypes.gevoedDoor = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
			AND assettypes.uri NOT IN ('https://lgc.data.wegenenverkeer.be/ns/installatie#RLC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SNC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Z30', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RSSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RVMSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#PKGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#ARS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CameraLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#WegPunt', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SlbGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SoftwareLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Kast', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CamGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#HS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#LS')
		GROUP BY 1 ), 
voedingsrelaties AS ( 
	SELECT DISTINCT doelUuid
	FROM assetrelaties
		INNER JOIN relatietypes ON assetrelaties.relatietype = relatietypes.uuid
	WHERE relatietypes.label = 'Voedt'), 
metVoedingsbron AS ( 
	SELECT CASE
		WHEN toezichtgroepen.naam IS NULL THEN '(onbekend)'
		ELSE toezichtgroepen.naam
		END AS toezichtgroep, 
	CURRENT_DATE AS tijdstip, COUNT(*) AS aantal, 'Met voedingsbron' AS titel
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN voedingsrelaties ON assets.uuid = voedingsrelaties.doelUuid
	WHERE assets.actief = TRUE AND voedingsrelaties.doelUuid IS NOT NULL AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%'
		AND assettypes.uri NOT IN ('https://lgc.data.wegenenverkeer.be/ns/installatie#RLC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SNC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Z30', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RSSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RVMSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#PKGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#ARS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CameraLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#WegPunt', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SlbGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SoftwareLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Kast', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CamGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#HS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#LS')
	GROUP BY 1 ), 
combinatie AS ( 
	SELECT * FROM totaal UNION ALL 
	SELECT * FROM metKenmerkBestek UNION ALL 
	SELECT * FROM metBestek UNION ALL 
	SELECT * FROM metKenmerkLocatie UNION ALL 
	SELECT * FROM metLocatie UNION ALL 
	SELECT * FROM metKenmerkBeheerder UNION ALL 
	SELECT * FROM metBeheerder UNION ALL 
	SELECT * FROM metKenmerkToezicht UNION ALL  
	SELECT * FROM metToezichter UNION ALL 
	SELECT * FROM metKenmerkGevoedGoor UNION ALL  
	SELECT * FROM metVoedingsbron), 
samengevoegd AS ( 
	SELECT CASE
		WHEN toezichtgroep = 'AWV_EW_AN' THEN 'TAW Antwerpen sectie EW'
		WHEN toezichtgroep = 'Tunnel Organ. VL.' THEN 'Tunnel Organisatie Vlaanderen'
		WHEN toezichtgroep = 'AWV_EW_LB' THEN 'TAW Limburg sectie EW'
		WHEN toezichtgroep = 'AWV_EW_OV' THEN 'TAW Oost Vlaanderen sectie EW'
		WHEN toezichtgroep = 'AWV_EW_VB' THEN 'TAW Vlaams Brabant sectie EW'
		WHEN toezichtgroep = 'AWV_EW_WV' THEN 'TAW West Vlaanderen sectie EW'
		WHEN toezichtgroep = 'EMT_BMI' THEN 'VC pijler Bewaking & Montoring Infra'
		WHEN toezichtgroep = 'EMT_TELE' THEN 'VWT sectie Netwerk en Telematica'
		WHEN toezichtgroep = 'EMT_VHS' THEN 'VWT sectie Verkeershandhavingsystemen'
		ELSE 'Andere toezichtgroepen'
	END AS toezichtgroep, tijdstip, aantal, titel
	FROM combinatie ) 
SELECT toezichtgroep, tijdstip::text, SUM(aantal) AS aantal, titel
FROM samengevoegd
GROUP BY 1, 2, 4;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
