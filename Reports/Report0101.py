from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0101(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0101',
                               title='Vplan koppelingen',
                               spreadsheet_id='17gA1IKf5VSF-HslE-C90l2msSNFzCsiakpcn-IlMDtI',
                               datasource='PostGIS',
                               link_type='eminfra',
                               persistent_column='R',
                               recalculate_cells=[('Dataconflicten', 'A1'), ('>10 jaar oud', 'A1')])

        self.report.result_query = """
            WITH vrs AS (
                SELECT
                    a.*,
                    l.geometry AS geom
                FROM assets a
                LEFT JOIN locatie l ON a.uuid = l.assetuuid
                WHERE a.assettype IN (
                    '13fa9473-f919-432a-bd00-bc19645bd30a',  -- Verkeersregelaar (Legacy)
                    '40f86745-ecaa-456b-8262-0a1f014602df'  -- ITSApp-RIS (Legacy)
                )
            )
            SELECT
                v.uuid,
                split_part(v.naampad, '/', 1) AS installatie,
                v.naampad,
                v.actief,
                v.toestand,
                l.adres_gemeente,
                l.adres_provincie,
                to_char(date(vplan.indienstdatum), 'yyyy-mm-dd') AS indienstdatum,
                CASE
                    WHEN vplan.uitdienstdatum IS NULL AND vplan.indienstdatum IS NOT NULL AND vplan.indienstdatum <= CURRENT_DATE THEN 'in dienst'
                    WHEN vplan.indienstdatum IS NOT NULL AND vplan.uitdienstdatum IS NOT NULL AND CURRENT_DATE BETWEEN vplan.indienstdatum AND vplan.uitdienstdatum THEN 'in dienst'
                    ELSE to_char(date(vplan.uitdienstdatum), 'yyyy-mm-dd')
                END AS uitdienstdatum,
                vplan.vplannummer AS vplan_nr,
                left(vplan.vplannummer, 7) AS vplan_nr_kort,
                vplan.commentaar,
                b.edeltadossiernummer,
                b.aannemernaam,
                (vplan.uitdienstdatum IS NULL AND vplan.indienstdatum <= CURRENT_DATE - INTERVAL '10 YEAR') AS "10_jaar_oud",
                CASE
                    WHEN vplan.uuid IS NULL AND v.actief = TRUE AND v.toestand = 'in-gebruik' THEN TRUE
                    WHEN vplan.uitdienstdatum IS NULL AND vplan.uuid IS NOT NULL AND v.actief = TRUE AND v.toestand NOT IN ('in-gebruik', 'overgedragen') THEN TRUE
                    WHEN (l.adres_provincie IS NULL OR l.geometry IS NULL) AND v.actief = TRUE THEN TRUE
                    ELSE FALSE
                END AS dataconflicten
            FROM vrs v
            LEFT JOIN locatie l ON v.uuid = l.assetuuid
            LEFT JOIN vplan_koppelingen vplan ON v.uuid = vplan.assetuuid
            LEFT JOIN bestekkoppelingen bk ON v.uuid = bk.assetuuid AND lower(bk.koppelingstatus) = 'actief'
            LEFT JOIN bestekken b ON bk.bestekuuid = b.uuid
            WHERE (vplan.uuid IS NOT NULL AND v.actief = FALSE) OR v.actief = TRUE
            ORDER BY v.actief DESC, dataconflicten, v.naampad, uitdienstdatum DESC;
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
