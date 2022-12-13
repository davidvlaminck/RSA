from DQReport import DQReport


class Report0058:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0058',
                               title='Er zijn geen assets die zichzelf direct of indirect voeden (geen lussen in voeding).',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            match (a:Asset {isActief: True}) - [:HoortBij] - (b {isActief: True}) where ((b:DNBHoogspanning) or (b:DNBLaagspanning)) 
            and  a.eanNummer <> b.eanNummer
            return  a.naampad as naampad 
            union 
            match (a:Asset {isActief: True}) - [:HoortBij] - (b {isActief: True}) where (b:DNBHoogspanning) or (b:DNBLaagspanning)
            with a, collect(b.eanNummer) as EAN, count(distinct b.eanNummer) as cnt where cnt > 1
            return a.naampad as naampad
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
