from DQReport import DQReport


class Report0121:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0121',
                               title='Netwerkpoorten hebben een unieke naam',
                               spreadsheet_id='1QPnohwuI7ziIFU2wac_9ZbOcJWr20asu4gvsr0t3x3E',
                               datasource='PostGIS',
                               persistent_column='I',
                               link_type='eminfra_onderdeel')

        self.report.result_query = """
                    WITH dubbele_namen AS (
            SELECT a.naam, count(*) AS aantal          
            FROM assets a 
            WHERE a.assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' -- Netwerkpoort
                AND a.actief = TRUE
            GROUP BY a.naam
            HAVING count(a.naam) > 1)
        SELECT
            a.uuid
            , a.naam
            , dubbele_namen.aantal
            , a2.waarde AS "type"
            , a3.waarde AS merk
            , b.edeltadossiernummer AS bestek_dossiernummer
            , b.edeltabesteknummer  AS bestek_besteknummer
            , b.aannemernaam AS bestek_aannemernaam
        FROM assets a
            INNER JOIN dubbele_namen ON dubbele_namen.naam = a.naam
            LEFT JOIN attribuutwaarden a2 ON a.uuid = a2.assetuuid AND a2.attribuutuuid = '97977fa6-732b-4222-94fa-b9723945bd79' -- Netwerkpoort.type
            LEFT JOIN attribuutwaarden a3 ON a.uuid = a3.assetuuid AND a3.attribuutuuid = '6db57eb2-e3ea-461f-812b-2d8fae7c2b0f' -- Netwerkpoort.merk	
            LEFT JOIN bestekkoppelingen bk ON a.uuid = bk.assetuuid 
            LEFT JOIN bestekken b ON bk.bestekuuid = b.uuid
        WHERE a.actief = TRUE AND a.assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' -- Netwerkpoort
        ORDER BY a.naam;

            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
