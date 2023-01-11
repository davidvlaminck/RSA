from DQReport import DQReport


class Report0001:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0001',
                               title='Onderdelen hebben een HoortBij relatie',
                               spreadsheet_id='16iUSRuS9M85P4E7Mi5-1J8pWgPr6Ehp1liEmRaZFNi4',
                               datasource='Neo4J',
                               persistent_column='D')

        # TODO feedback: bevestigingsbeugel en omvormer weghalen (omvormer naar camera moet wel aanwezig zijn)
        self.report.result_query = """
MATCH (pk:Asset {isActief: TRUE})-[:Bevestiging]-(:Netwerkelement {isActief: TRUE})-[:HoortBij]->(:Asset {isActief: TRUE}) 
WHERE pk:Netwerkpoort OR pk:Netwerkkaart
WITH collect(pk) as poortofkaart
MATCH (a:onderdeel {isActief: TRUE}) 
WHERE NOT EXISTS((a)-[:HoortBij]->(:Asset {isActief: TRUE})) AND NOT a IN poortofkaart
RETURN a.uuid, a.naam, a.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
