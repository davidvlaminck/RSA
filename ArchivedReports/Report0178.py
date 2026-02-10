from lib.reports.DQReport import DQReport


class Report0178:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0178', title='Bestekken zonder aannemer',
                               spreadsheet_id='17fa88iF8f6kQYJW49nkn_mkZSJW02kGsCMXtpHBLbJU', datasource='PostGIS',
                               persistent_column='E')

        self.report.result_query = """
	select uuid as bestekuuid, edeltadossiernummer, edeltabesteknummer, aannemernaam
	from bestekken
	where aannemernaam is null
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
