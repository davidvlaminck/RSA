from DQReport import DQReport


class Report0106:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0106', title='Geometrie niet consistent met GeometrieArtefact',
                               spreadsheet_id='1x9g0b_wQtLgkxnAwR_lffzVLdS3PElb3mLWtqItqkig', datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
