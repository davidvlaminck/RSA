from DQReport import DQReport


class Report0101:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0101',
                               title='Vplan koppelingen',
                               spreadsheet_id='17gA1IKf5VSF-HslE-C90l2msSNFzCsiakpcn-IlMDtI',
                               datasource='PostGIS',
                               link_type='eminfra',
                               persistent_column='R',
                               recalculate_cells=[('Dataconflicten', 'A1'), ('>10 jaar oud', 'A1')])

        self.report.result_query = """
WITH vrs AS (
    SELECT assets.*, ST_SETSRID(ST_MakePoint(cast(x as float), cast(y as float)), 31370) AS geom
    FROM assets 
        LEFT JOIN locatie ON assets.uuid = locatie.assetuuid
    WHERE assettype IN ('13fa9473-f919-432a-bd00-bc19645bd30a','40f86745-ecaa-456b-8262-0a1f014602df'))
SELECT vrs.uuid as em_infra_link, split_part(naampad, '/', 1) AS installatie, actief, toestand, ST_X(ST_Transform(geom, 4326)) AS longitude, ST_Y(ST_Transform(geom, 4326)) AS latitude
    , locatie.adres_gemeente, locatie.adres_provincie, text(date(indienstdatum)) AS indienstdatum
    , CASE WHEN uitdienstdatum IS NULL AND indienstdatum IS NOT NULL AND indienstdatum <= CURRENT_DATE THEN text('in dienst') ELSE to_char(date(uitdienstdatum), 'yyyy-mm-dd') END AS uitdienstdatum
    , vplannummer AS vplan_nr, left(vplannummer, 7) AS vplan_kort, vplan_koppelingen.commentaar AS commentaar
    , bestekken.edeltadossiernummer, bestekken.aannemernaam
    , CASE WHEN uitdienstdatum IS NULL AND indienstdatum <= CURRENT_DATE - INTERVAL '10' YEAR THEN TRUE ELSE FALSE END AS "10_jaar_oud"
    , CASE WHEN vplan_koppelingen.uuid IS NULL AND actief = TRUE AND toestand = 'in-gebruik' THEN TRUE
        WHEN uitdienstdatum IS NULL AND vplan_koppelingen.uuid IS NOT NULL AND actief = TRUE AND toestand <> 'in-gebruik' AND toestand <> 'overgedragen' THEN TRUE
        WHEN locatie.adres_provincie IS NULL OR locatie.x IS NULL AND actief = TRUE THEN TRUE
        ELSE FALSE END AS dataconflicten
FROM vrs
    LEFT JOIN locatie ON vrs.uuid = locatie.assetuuid
    LEFT JOIN vplan_koppelingen ON vrs.uuid = vplan_koppelingen.assetuuid
    LEFT JOIN bestekkoppelingen ON vrs.uuid = bestekkoppelingen.assetuuid AND bestekkoppelingen.koppelingstatus = 'ACTIEF'
    LEFT JOIN bestekken ON bestekkoppelingen.bestekuuid = bestekken.uuid
WHERE (vplan_koppelingen.uuid IS NOT NULL AND actief = FALSE) OR actief = TRUE
ORDER BY actief DESC, dataconflicten, naampad;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
