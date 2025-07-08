from DQReport import DQReport


class Report0195:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0195',
                               title='Kast (Legacy) hebben een locatie',
                               spreadsheet_id='1xFCTQpOty0ur3Tgn-rYmHs4jonZkA5l794Neid1kaCw',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
        select
            a.uuid
            , a.toestand
            , a.actief
            , a.naam
            , a.commentaar 
            , i.gebruikersnaam
            , l.geometry
        from assets a
        left join locatie l on a."uuid" = l.assetuuid
        left join identiteiten i on a.toezichter = i."uuid" 
        where
            a.assettype = '10377658-776f-4c21-a294-6c740b9f655e' -- Kast (Legacy)
            and
            a.actief = true
            and
            l.geometry is null
        order by
            a.toestand, i.gebruikersnaam 
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
