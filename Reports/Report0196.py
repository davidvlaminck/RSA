from DQReport import DQReport


class Report0196:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0196',
                               title='Lichtmast heeft een locatie',
                               spreadsheet_id='1dgAGfvuGBCnW4oWXm0eUJMqSv6PXbbtAEEmNNUdOmwk',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a.uuid
                , a.toestand
                , a.actief
                , a.naam
                , a.naampad
                , a.commentaar 
                , g.geometry
            from assets a
            left join geometrie g on a.uuid = g.assetuuid
            where
                a.assettype = '8d9f83fa-0e19-47ec-902f-ac2c538dd6d9' -- Lichtmast
                and
                a.actief = true
                and
                g.geometry is null
            order by
                a.naampad
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
