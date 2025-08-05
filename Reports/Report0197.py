from DQReport import DQReport


class Report0197:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0197',
                               title='Asset (OTL) heeft een inactieve toezichter',
                               spreadsheet_id='1fyJRTZc_yDiC5h1BRzJvW0AxWJxaSVL5CK5ETbGdXc0',
                               datasource='PostGIS',
                               persistent_column='J',
                               link_type='eminfra')

        self.report.result_query = """
            -- Legacy: identiteiten
            with cte_identiteit_inactief as (
                -- alle inactieve records uit tabel identiteit
                select i.*
                from identiteiten i
                where i.actief is false
            )
            -- main query
            -- test select query
            --select * from cte_identiteit;
            select
                a."uuid" 
                , at.uri
                , a.toestand 
                , a.actief
                , a.naampad 
                , a.naam 
                , a.commentaar 
                , i.gebruikersnaam 
                , i.naam || ' ' || i.voornaam as "gebruikersnaam voluit"
            from assets a 
            inner join cte_identiteit_inactief i on a.toezichter = i."uuid"
            left join assettypes at on a.assettype = at."uuid" 
            where a.actief is true
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
