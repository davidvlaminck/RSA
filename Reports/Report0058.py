from DQReport import DQReport


class Report0058:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0058',
                               title='Er zijn geen assets die het doel zijn van twee of meer Voedt relaties.',
                               spreadsheet_id='15knbCKB7xWKDX_7utnDBsNe2mYHxGwM6cl8bPwg6q5k',
                               datasource='Neo4J',
                               persistent_column='H')

        self.report.result_query = """
            MATCH (a {isActief: TRUE})<-[:Voedt]-(v {isActief: TRUE})
            WHERE NOT (v:onderdeel) AND NOT (v:UPSLegacy)
            WITH a, count(v) as v_count 
            WHERE v_count > 1 
            RETURN 
                DISTINCT a.uuid as uuid, a.naampad as naampad, a.toestand as toestand, 
                a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email,
                a.`tz:toezichtgroep.tz:naam` as tzg_naam,  a.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


# to verify
aql_query = """
FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true

  LET voeders = (
    FOR v, rel IN INBOUND a voedt_relaties
      RETURN v
  )

  FILTER LENGTH(voeders) > 1

  RETURN DISTINCT {
    uuid: a._key,
    naampad: a.AIMNaamObject_naampad,
    toestand: a.toestand,
    tz_voornaam: a["tz:toezichter.tz:voornaam"],
    tz_naam: a["tz:toezichter.tz:naam"],
    tz_email: a["tz:toezichter.tz:email"],
    tzg_naam: a["tz:toezichtgroep.tz:naam"],
    tzg_referentie: a["tz:toezichtgroep.tz:referentie"]
  }
"""

