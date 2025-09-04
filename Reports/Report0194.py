from DQReport import DQReport


class Report0194:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0194',
                               title='CabineControllers (Afstandsbewaking) hebben een (afgeleide) locatie',
                               spreadsheet_id='1P-6URGL4nQujCzeeuHq50GMLWYRpMCXaf9gjouYTLMU',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
        select
            a."uuid"
            , a.actief 
            , a.toestand 
            , a.naam 
            , at."label" 
            , l.geometrie  
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        left join locatie l on a."uuid" = l.assetuuid
        where
            a.actief is true
            and a.assettype = '8eda4230-e7dc-4b72-b02b-26d81aa1f45e' -- Afstandsbewaking (Legacy)
            and l.geometry is null
        order by a.toestand, a.naam
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
