from DQReport import DQReport


class Report0060:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0060',
                               title='Het EAN nummer van een DNBLaagspanning of DNBHoogspanning is geldig..',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='I')

        self.report.result_query = """
            WITH a, split(a.eanNummer, "") as split_ean
            WITH a, split_ean, reduce(
                    acc = [0, 0, 0], 
                    n IN split_ean[0..-1] | [acc[0] + 1, acc[1] + ((acc[0] + 1) % 2) * toInteger(n), acc[2] + (acc[0] % 2) * toInteger(n)]
                ) as running_sums
            WITH a, ((3 * running_sums[1] + running_sums[2] + toInteger(last(split_ean))) % 10) = 0 as is_valid_ean
            WHERE 
                (a:DNBLaagspanning OR a:DNBHoogspanning)
                AND (a.eanNummer IS NOT NULL) 
                AND (NOT (a.eanNummer =~ '^54\d{16}$' OR a.eanNummer =~ '^54\d{10}$') OR NOT is_valid_ean)
            RETURN a.uuid as uuid, a.naam as naam, a.typeURI as typeURI, a.toestand as toestand, a.eanNummer as eanNummer, a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
