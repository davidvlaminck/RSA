from DQReport import DQReport


class Report0144:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0144',
                               title='',
                               spreadsheet_id='1jXwjdnox1cb-uh-tJMP2BuZwrrxCL0StjZspjVw9MGQ',
                               datasource='PostGIS',
                               persistent_column='I'
                               )

        self.report.result_query = """
        select
            a."uuid"
            , a.naam
            , a.naampad
            , case 
                when naampad ~ '.*TUNNEL.*' then true
                else False		
            end as "isTunnel"
            , a.toestand 
            , at.naam assettype_naam
            , ea.ean
            , ea.aansluiting
        from assets a 
        inner join elek_aansluitingen ea on a.uuid = ea.assetuuid 
        left join assettypes at on a.assettype = at."uuid" 
        where
            a.actief = true
            and 
            ea.ean is not null
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
