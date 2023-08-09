from DQReport import DQReport


class Report0021:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0021',
                               title='OTN Netwerkelement verband HoortBij relaties en merk',
                               spreadsheet_id='1WZA7Gds7jikM-I-rFGds0thDx7y_osadLluGKF9rHN8',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """OPTIONAL MATCH (n:Netwerkelement {isActief:TRUE})-[h:HoortBij]->(i:installatie {isActief:TRUE})
        WHERE (n.merk IN ['NOKIA', 'Ciena', 'Edge'] AND (h IS NULL OR NOT(i:SDH OR i:CEN OR i:OTN))) OR ((i:SDH OR i:CEN OR i:OTN) AND NOT (n.merk in ['NOKIA', 'Ciena', 'Edge']))
        RETURN n.uuid, n.naam, n.merk, i.uuid as installatie_uuid, i.naampad as installatie_naampad, i.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
