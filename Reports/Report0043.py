from DQReport import DQReport


class Report0043:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0043',
                               title='Er zijn geen instanties van classes die deprecated zijn in de OTL',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='D')

        # TODO: refactor so list is not hardcoded
        self.report.result_query = """MATCH (x) 
            UNWIND labels(x) as label
            WITH x, label
            WHERE label IN [
                "Betonfundering", "GeluidswerendeConstructie", "Doorgang", "Bovenbouw", "FieldOfView", 
                "OpgaandeBoom", "Exoten", "ProefVoertuigOverhelling", "ProefSchokindex", "ProefKerendVermogen",
                "ProefPerformantieniveau", "ProefWerkingsbreedteMVP", "ProefPerformantieKlasse", "ProefWerkingsbreedteGC"]
            RETURN x.uuid as uuid, x.naam as naam, x.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
