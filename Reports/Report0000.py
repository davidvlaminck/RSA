from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0000(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0000',
                               title="testsheet (dev only)",
                               spreadsheet_id='1SK0UVeKnJe0eQaktKMFjeJSg16wZ4SAW-W8wz16x3Tg',
                               datasource='PostGIS',
                               convert_columns_to_numbers=['B', 'C'])

        self.report.result_query = """
               WITH t1 as (
        SELECT 'tekst' as col1, 
        1::numeric as col2 FROM assets LIMIT 5),
        t2 as (
        SELECT 'tekst' as col1, 
        NULL::numeric as col2 FROM assets LIMIT 5),
        t AS (SELECT * FROM t2 UNION ALL SELECT * FROM t1)       
        SELECT *,		
        CASE WHEN col2 IS NOT NULL THEN col2::NUMERIC
			ELSE 1::NUMERIC END AS aantal_verlichtingstoestellen_getal FROM t ;"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
