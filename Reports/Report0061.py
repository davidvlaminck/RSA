from DQReport import DQReport


class Report0061:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0061',
                               title='Het EAN nummer van een DNBLaagspanning of DNBHoogspanning is geldig (checksum).',
                               spreadsheet_id='1M8NE8RxnEJdG-8suCjKOzh96O6pGUcfmFi83ePO3glc',
                               datasource='Neo4J',
                               persistent_column='L',
                               link_type='eminfra')

        self.report.result_query = """
            MATCH (a:Asset {isActief: TRUE})
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
            RETURN 
                a.uuid as uuid, a.naam as naam, a.typeURI as typeURI, a.toestand as toestand, 
                a.eanNummer as eanNummer, 
                CASE 
                    WHEN right(a.eanNummer, 1) = " " THEN "trailing whitespace(s)" 
                    WHEN left(a.eanNummer, 1) = " " THEN "leading whitespace(s)" 
                    ELSE "invalid EAN" 
                    END AS reason_invalid, 
                a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email, 
                a.`tz:toezichtgroep.tz:naam` as tzg_naam,  a.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
