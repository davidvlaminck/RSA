from lib.reports.DQReport import DQReport


class Report0060:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET dnb_keys = (
  FOR at IN assettypes
    FILTER at.short_uri IN ["onderdeel#DNBHoogspanning","onderdeel#DNBLaagspanning"]
    RETURN at._key
)

LET duplicateEans = (
  FOR a IN assets
    FILTER a.AIMDBStatus_isActief == true
      AND a.DNB_eanNummer != null
      AND a.DNB_eanNummer != ""
    COLLECT ean = a.DNB_eanNummer WITH COUNT INTO cnt
    FILTER cnt > 1
    RETURN ean
)

FOR d IN assets
  FILTER
    d.AIMDBStatus_isActief == true
    AND d.assettype_key IN dnb_keys
    AND d.DNB_eanNummer IN duplicateEans
  RETURN {
    uuid: d._key,
    naampad: d.AIMNaamObject_naampad,
    toestand: d.toestand,
    tz_voornaam: d["tz:toezichter.tz:voornaam"],
    tz_naam: d["tz:toezichter.tz:naam"],
    tz_email: d["tz:toezichter.tz:email"],
    tzg_naam: d["tz:toezichtgroep.tz:naam"],
    tzg_referentie: d["tz:toezichtgroep.tz:referentie"]
  }
"""
        self.report = DQReport(name='report0060',
                               title='Er zijn geen conflicten tussen EAN-nummers (dubbel EAN-nummer).',
                               spreadsheet_id='1od9125ZSoFG6fGwvoS8CSCz-Bne4N8vVBXORjYhtjQY',
                               datasource='ArangoDB',
                               persistent_column='I',
                               link_type='eminfra')

        self.report.result_query = aql_query
        self.report.cypher_query = """
            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) \n            WHERE ((y:DNBHoogspanning) OR (y:DNBLaagspanning)) AND  x.eanNummer <> y.eanNummer\n            RETURN \n                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, \n                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,\n                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie\n            UNION \n            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) \n            WHERE (y:DNBHoogspanning) OR (y:DNBLaagspanning)\n            WITH x, count(DISTINCT y.eanNummer) as ean_count \n            WHERE ean_count > 1\n            RETURN \n                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, \n                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,\n                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie\n        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
