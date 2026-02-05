from lib.reports.LegacyHistoryReport import LegacyHistoryReport


class Report0068:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = LegacyHistoryReport(name='report0068',
                                          title="Detailrapport invulgraad legacy installaties EW Antwerpen",
                                          spreadsheet_id='1y3XdYwNqFcyRNa9SHFs-d7DSGVJbWYI8sM9EzE1gBgE',
                                          datasource='PostGIS',
                                          frequency=7,
                                          persistent_column='K')

        self.report.result_query = """
WITH bestek_koppelingen AS ( 
	SELECT DISTINCT assetuuid 
	FROM bestekkoppelingen
	WHERE lower(koppelingstatus) = 'actief'), 
voedingsrelaties AS ( 
	SELECT DISTINCT doelUuid
	FROM assetrelaties
		INNER JOIN relatietypes ON assetrelaties.relatietype = relatietypes.uuid
	WHERE relatietypes.label = 'Voedt'), 
records AS ( 
	SELECT assets.uuid, naampad, assettypes.LABEL AS "type", assets.toestand , 
		CASE WHEN assettypes.toezicht = TRUE AND identiteiten.gebruikersnaam  IS NULL THEN '1' ELSE '0' END AS zonder_toezichter, 
		CASE WHEN assettypes.bestek = TRUE AND bestek_koppelingen.assetUuid IS NULL THEN '1' ELSE '0' END AS zonder_bestek, 
		CASE WHEN assettypes.locatie = TRUE AND (locatie.x IS NULL OR locatie.x = 0) THEN '1' ELSE '0' END AS zonder_locatie, 
		CASE WHEN assettypes.beheerder = TRUE AND beheerders.uuid IS NULL THEN '1' ELSE '0' END AS zonder_beheerder, 
		CASE WHEN assettypes.gevoedDoor = TRUE AND voedingsrelaties.doelUuid IS NULL 
			AND assettypes.uri NOT IN ('https://lgc.data.wegenenverkeer.be/ns/installatie#RLC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SNC', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Z30', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RSSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#RVMSGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#PKGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#ARS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CameraLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#WegPunt', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SlbGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#SoftwareLegacy', 'https://lgc.data.wegenenverkeer.be/ns/installatie#Kast', 'https://lgc.data.wegenenverkeer.be/ns/installatie#CamGroep', 'https://lgc.data.wegenenverkeer.be/ns/installatie#LS', 'https://lgc.data.wegenenverkeer.be/ns/installatie#HS')
			THEN '1' ELSE '0' END AS zonder_voeding, 
		identiteiten.gebruikersnaam AS toezichter
	FROM assets
		LEFT JOIN toezichtgroepen ON assets.toezichtgroep = toezichtgroepen.uuid
		LEFT JOIN identiteiten ON assets.toezichter = identiteiten.uuid
		LEFT JOIN assettypes ON assets.assettype = assettypes.uuid
		LEFT JOIN voedingsrelaties ON assets.uuid = voedingsrelaties.doelUuid
		LEFT JOIN beheerders ON assets.schadebeheerder = beheerders.uuid
		LEFT JOIN bestek_koppelingen ON assets.uuid = bestek_koppelingen.assetUuid
		LEFT JOIN locatie ON assets.uuid = locatie.assetuuid 
	WHERE assets.actief = TRUE AND assettypes.uri NOT LIKE 'https://grp%' AND assettypes.uri NOT LIKE 'https://wegen%' AND toezichtgroepen.referentie = 'AWV_EW_AN' ) 
SELECT *
FROM records
WHERE zonder_toezichter = '1' OR zonder_bestek = '1' OR zonder_locatie = '1' OR zonder_beheerder = '1' OR zonder_voeding = '1';
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
