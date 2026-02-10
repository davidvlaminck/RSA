from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0143(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0143',
                               title='Boom zonder naam',
                               spreadsheet_id='1Vnn-fHvk0NtnmIeDXtTYByzna5qy62qz6zTZDSCxFos',
                               datasource='PostGIS',
                               persistent_column='D'
                               )

        self.report.result_query = """
        /*
         * Boom zonder naam
         * */
        select
            a."uuid" 
            , a.naam
            , a.commentaar
        from assets a
        where
            a.assettype = 'cd77f043-dc69-46ae-98a1-da8443ca26bf'
            and
            a.actief = true 
            and
            (a.naam = '' or a.naam is null)
        order by naam asc
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
