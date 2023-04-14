from DQReport import DQReport


class Report0078:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0078',
                               title='Verkeersregelaars hebben een coördinatiewijze',
                               spreadsheet_id='1uhl_HnxT5H9XrEjswHlkR_jvl4nx99ss9UOM-3Yjy_M',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) 
WHERE a.`coordinatiewijze[0]` IS NULL
RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
