from lib.reports.DQReport import DQReport


class Report0061:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET dnbhoogspanning_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#DNBHoogspanning\" LIMIT 1 RETURN at._key)
LET dnlaagspanning_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#DNBLaagspanning\" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.AIMDBStatus_isActief == true
    AND (a.assettype_key == dnbhoogspanning_key OR a.assettype_key == dnlaagspanning_key)
    AND a.DNB_eanNummer != null

  LET ean_str = a.DNB_eanNummer
  LET ean_arr = SPLIT(ean_str, "")
  LET ean_len = LENGTH(ean_arr)
  LET last_digit = TO_NUMBER(ean_arr[ean_len - 1])

  // Cypher parity logic: index starts at 0, but Cypher increments before testing
  LET running_sums = (
    FOR i IN 0..(ean_len - 2)
      LET n = TO_NUMBER(ean_arr[i])
      LET pos = i + 1
      RETURN {
        odd_sum:  (pos % 2 == 1 ? n : 0),   // matches Cypher's (acc[0] + 1) % 2
        even_sum: (pos % 2 == 0 ? n : 0)
      }
  )

  LET odd_sum  = SUM(running_sums[*].odd_sum)
  LET even_sum = SUM(running_sums[*].even_sum)

  LET is_valid_ean = ((3 * odd_sum + even_sum + last_digit) % 10) == 0

  FILTER
    (
      NOT (
        REGEX_TEST(ean_str, "^54\\d{16}$") 
        OR 
        REGEX_TEST(ean_str, "^54\\d{10}$")
      )
    )
    OR NOT is_valid_ean

  LET reason_invalid =
    ean_str[LENGTH(ean_str)-1] == " " ? "trailing whitespace(s)" :
    ean_str[0] == " " ? "leading whitespace(s)" :
    "invalid EAN"

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam,
    typeURI: a.typeURI,
    toestand: a.toestand,
    eanNummer: a.DNB_eanNummer,
    reason_invalid: reason_invalid,
    tz_voornaam: a[\"tz:toezichter.tz:voornaam\"],
    tz_naam: a[\"tz:toezichter.tz:naam\"],
    tz_email: a[\"tz:toezichter.tz:email\"],
    tzg_naam: a[\"tz:toezichtgroep.tz:naam\"],
    tzg_referentie: a[\"tz:toezichtgroep.tz:referentie\"]
  }
"""
        self.report = DQReport(name='report0061',
                               title='Het EAN nummer van een DNBLaagspanning of DNBHoogspanning is geldig (checksum).',
                               spreadsheet_id='1M8NE8RxnEJdG-8suCjKOzh96O6pGUcfmFi83ePO3glc',
                               datasource='ArangoDB',
                               persistent_column='L',
                               link_type='eminfra')

        self.report.result_query = aql_query
        self.report.cypher_query = """
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
                AND (NOT (a.eanNummer =~ '^54\\d{16}$' OR a.eanNummer =~ '^54\\d{10}$') OR NOT is_valid_ean)
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
