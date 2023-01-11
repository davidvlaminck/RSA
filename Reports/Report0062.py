from DQReport import DQReport


class Report0062:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0062',
                               title="Failover assets",
                               spreadsheet_id='1hX4KW6lRgUWb-uhtmdmBVeHUb-7xDs1Mg5sCvMZ-jhA',
                               datasource='PostGIS',
                               persistent_column='K')

        self.report.result_query = """
WITH failovertypes AS (SELECT * FROM assettypes WHERE uri IN 
    ('https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#ActivityComplex',
    'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#ElectricityAppurtenance',
    'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#ElectricityCable',
    'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#TelecommunicationsAppurtenance',
    'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#TelecommunicationsCable',
    'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#Pipe'))
SELECT a.uuid, failovertypes.naam, b.uuid as legacy_uuid, b.naampad, b.actief, b.toestand, assettypes."label" AS legacy_afkorting, 
    assettypes.naam AS legacy_type,	toezichtgroepen.referentie AS toezichtgroep, 
    identiteiten.voornaam || ' ' || identiteiten.naam AS toezichter
FROM failovertypes 
	LEFT JOIN assets a ON a.assettype = failovertypes.uuid AND a.actief = TRUE
	LEFT JOIN assetrelaties ON a.uuid = assetrelaties.bronuuid AND assetrelaties.relatietype = 
	    '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2' AND assetrelaties.actief = TRUE
	LEFT JOIN assets b ON b.uuid  = assetrelaties.doeluuid
	LEFT JOIN assettypes ON b.assettype = assettypes.uuid  
	LEFT JOIN toezichtgroepen ON b.toezichtgroep = toezichtgroepen.uuid 
	LEFT JOIN identiteiten ON b.toezichter = identiteiten.uuid;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
