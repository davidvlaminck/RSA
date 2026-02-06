from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0173(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0173',
                               title='Legacy assets ontbreken een naampad',
                               spreadsheet_id='1Lu1nSafM08GgwY1FHd4vnEN6qbS0Z4lI-H96gZzV8Z0',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra'
                               )

        self.report.result_query = """
        select
            a."uuid"
            , a.toestand
            , a.actief 
            , a.naam
            , a.naampad
            , at.naam as assettype_naam
            , at.uri as assettype_uri
        from assets a
        left join assettypes at on a.assettype = at."uuid" 
        where
            a.actief is true 
            and
            a.naampad is null
            and
            at.uri ~ '^https://lgc.data.wegenenverkeer.be'
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
