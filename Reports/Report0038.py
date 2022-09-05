from DQReport import DQReport


class Report0038:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0038',
                               title="IP AS1 elementen hebben een .ODF TT tegenhanger",
                               spreadsheet_id='1rDCUE7kj0ZcCVtFe2EiIqKMz7fdR5J6mtpU6lRpzpbI',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (i:IP {isActief:TRUE})
        WHERE i.naam contains '.AS1'
        WITH i, split(i.naampad,'/') AS splitted
        WITH i, apoc.text.join(reverse(tail(reverse(splitted))),'/') + '/' AS naampad_beh
        OPTIONAL MATCH (t:TT {isActief:TRUE})
        WHERE t.naampad contains naampad_beh AND t.naam contains 'ODF'
        WITH i, t
        WHERE t.uuid IS NULL
        RETURN i.uuid, i.naampad, i.`tz:toezichter.tz:gebruikersnaam` AS toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

