from lib.reports.DQReport import DQReport


class Report0212:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0212',
                               title='Assets met DA- in diens naampad',
                               spreadsheet_id='1F4lMZPKRjWWEq7Q5dbjO4lN1yBD_VNs-LXC3X56CoQ4',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
                select
                    a."uuid",
                    a.naampad,
                    a.naam, 
                    a.actief,
                    a.assettype,
                    a.commentaar 
                from assets a
                where lower(a.naampad) like '%da-202%' and a.actief is true
                order by naampad asc
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
