from DQReport import DQReport


class Report0022:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0022',
                               title='OTN Netwerkelement naamgeving',
                               spreadsheet_id='1R3nwwFJxCYVOMAeX79E_U_9X3Uda3_oKMQQQzEMPmVI',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """MATCH (n:Netwerkelement {isActief:TRUE})-[h:HoortBij]->(i:installatie {isActief:TRUE})
        WHERE (i:SDH OR i:CEN OR i:OTN)
        WITH *, split(i.typeURI, '#')[1] AS OTN_type
        WHERE (OTN_type = 'SDH' and NOT n.naam STARTS WITH 'BELFLA') 
        OR (OTN_type = 'CEN' and NOT n.naam STARTS WITH 'CEN')
        OR (OTN_type = 'OTN' and NOT (n.naam STARTS WITH 'OTN' OR n.naam STARTS WITH 'CPO'))
        RETURN n.uuid, n.naam, n.merk, i.uuid as installatie_uuid, i.naampad as installatie_naampad, i.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
