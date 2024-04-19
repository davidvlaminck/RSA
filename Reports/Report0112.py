from DQReport import DQReport


class Report0112:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0112', title='Verkeersregelaars hebben een vplanDatum',
                               spreadsheet_id='1701KVEMJAco3NPxfgOtHP0byI9_MQ1yhb1EQ3ujvU9I', datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
        // Verkeersregelaars hebben een vplanDatum
        MATCH (a:Verkeersregelaar {isActief:TRUE}) 
        WHERE a.vplanDatum is null
        RETURN a.uuid, a.naam, a.vplanNummer, a.vplanDatum
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
