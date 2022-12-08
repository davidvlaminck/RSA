from DQReport import DQReport


class Report0057:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0057',
                               title='Er zijn geen assets die het doel zijn van twee of meer Voedt relaties.',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """
            MATCH (a {isActief: TRUE})<-[:Voedt]-(v {isActief: TRUE})
            WHERE NOT (v:onderdeel) AND NOT (v:UPSLegacy)
            WITH a, count(v) as v_count 
            WHERE v_count > 1
            RETURN DISTINCT a.uuid as uuid, a.naampad as naampad, a.toestand as toestand, a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
