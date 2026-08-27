from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0058(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        FOR edge IN voedt_relaties
          FILTER CONTAINS(edge._to, "assets/")
          COLLECT a_id = edge._to WITH COUNT INTO voeders_count
          FILTER voeders_count > 1
          LET a_doc = DOCUMENT(a_id)
          FILTER a_doc != null AND a_doc.AIMDBStatus_isActief == true
          LET voeders = (
            FOR v IN voedt_relaties
              FILTER v._to == a_id
              LET v_doc = DOCUMENT(v._from)
              FILTER v_doc != null AND v_doc.AIMDBStatus_isActief == true
              RETURN v_doc
          )
          FILTER LENGTH(voeders) > 1
          RETURN {
            uuid: a_doc._key,
            naampad: a_doc.AIMNaamObject_naampad,
            toestand: a_doc.toestand,
            tz_voornaam: a_doc["tz:toezichter.tz:voornaam"],
            tz_naam: a_doc["tz:toezichter.tz:naam"],
            tz_email: a_doc["tz:toezichter.tz:email"],
            tzg_naam: a_doc["tz:toezichtgroep.tz:naam"],
            tzg_referentie: a_doc["tz:toezichtgroep.tz:referentie"]
          }
        """
        self.report = DQReport(name='report0058',
                               title='Er zijn geen assets die het doel zijn van twee of meer Voedt relaties.',
                               spreadsheet_id='15knbCKB7xWKDX_7utnDBsNe2mYHxGwM6cl8bPwg6q5k',
                               datasource='ArangoDB',
                               persistent_column='H',
                               excel_filename='[RSA] Assets met dubbele voeding.xlsx',)

        self.report.result_query = aql_query
        self.report.cypher_query = """
            MATCH (a {isActief: TRUE})<-[:Voedt]-(v {isActief: TRUE})
            WITH a, count(v) as v_count 
            WHERE v_count > 1 
            RETURN 
                DISTINCT a.uuid as uuid, a.naampad as naampad, a.toestand as toestand, 
                a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email,
                a.`tz:toezichtgroep.tz:naam` as tzg_naam,  a.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
