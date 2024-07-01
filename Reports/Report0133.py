from DQReport import DQReport


class Report0133:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0133',
                               title='Dubbele bomen',
                               spreadsheet_id='1rh9WX_zT9KjLPac9B4jg5p5rXKDBRlMIlkJVZKoQWd4',
                               datasource='PostGIS',
                               persistent_column='J'
                               )

        self.report.result_query = """

            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
