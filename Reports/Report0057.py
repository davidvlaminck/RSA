from DQReport import DQReport


class Report0057:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0057',
                               title='Er zijn geen attributen met de waarde -99999.99 (indicatie voor lege waarde).',
                               spreadsheet_id='1aLox-JNzTrwqNzexO6eygpbsUOyqeyy79T6SLUnsLHw',
                               datasource='PostGIS',
                               persistent_column='F')

        self.report.result_query = """
            SELECT ass.uuid AS asset_uuid, ass.naam AS asset_naam, ass_t.uri AS asset_type_uri, att.naam AS attribuut_naam, att_w.waarde AS attribuut_waarde
            FROM attribuutwaarden att_w
            INNER JOIN attributen att ON (att_w.attribuutuuid = att.uuid)
            INNER JOIN assets ass ON (att_w.assetuuid = ass.uuid)
            INNER JOIN assettypes ass_t ON (ass.assettype = ass_t.uuid)
            WHERE att_w.waarde LIKE '-99999.99'
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
