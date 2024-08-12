from DQReport import DQReport


class Report0030:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0030',
                               title='Netwerkelementen hebben een (afgeleide) locatie',
                               spreadsheet_id='1ZAZ8chzMbLEyGd-cbZM6S7Uw4aNOrBmAE1KWnbyvdK4',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkelement {isActief:TRUE})
        WHERE n.geometry IS NULL or n.geometry = ''
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
