from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0177(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0177', title='Actieve assets met toestand verwijderd (zichtbaar in Elisa-Infra)',
                               spreadsheet_id='1sM-Xm7gCtXo9duBF-zcSmIOPja1B4cSzDibJpaJ7WOE', datasource='PostGIS',
                               persistent_column='E')

        self.report.result_query = """
SELECT
	uuid, naam, actief, toestand
FROM assets a
WHERE a.actief = TRUE
AND a.toestand = 'verwijderd'
	    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
