from DQReport import DQReport


class Report0106:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0113', title='Dubbele geometrie - Galgpaal',
                               spreadsheet_id='1QpiwBAmNRIi-GP4EDfIUxMI_LV-qMMnjwzzaYk-ZoBc', datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
        with cte_assettypesOfInterest as (
            select uuid, label, uri 
            from assettypes
            where uri in (
                'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Galgpaal'
            )
        )
        select
            a."uuid"
            , a.naam
            , g.wkt_string
        from assets a
        left join geometrie g on a.uuid = g.assetuuid
        where g.wkt_string in (
            select g.wkt_string
            from assets a
            left join geometrie g on a.uuid = g.assetuuid
            where a.assettype in (select uuid from cte_assettypesOfInterest)
            group by g.wkt_string
            having count(g.wkt_string) > 1
            )
        and a.assettype in (select uuid from cte_assettypesOfInterest)
        order by g.wkt_string
        ;
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
