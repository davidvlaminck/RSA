from DQReport import DQReport


class Report0009:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0009',
                               title='Omvormers hebben een Bevestiging relatie met een Behuizing',
                               spreadsheet_id='1A4kata3Eg9fMjsUE8Za5XEtcF7JEm_-IftHhGz6SnJo',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """MATCH (o:Omvormer {isActief:TRUE})
        WHERE NOT EXISTS ((o)-[:Bevestiging]-(:Wegkantkast {isActief:TRUE})) AND NOT EXISTS ((o)-[:Bevestiging]-(:Montagekast {isActief:TRUE}))
        WITH o
        OPTIONAL MATCH (o)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        OPTIONAL MATCH (o)-[:Bevestiging]->(b:onderdeel {isActief:TRUE})
        RETURN o.uuid, o.naam, a.naam as toezichter, b.typeURI as behuizing_type"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
