from DQReport import DQReport


class Report0076:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0076',
                               title='Verkeersregelaars hebben een installatieverantwoordelijke',
                               spreadsheet_id='1JGhVFeXXejMHRupSqqKgSEaz384vf4NNrJ8OyDs4NeM',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE})
        WHERE NOT EXISTS ((a)-[:HeeftBetrokkene {rol:'installatieverantwoordelijke'}]->(:Agent))
        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
