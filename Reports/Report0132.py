from DQReport import DQReport


class Report0132:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0132',
                               title='Actieve assets hebben een bijpassende AIMToestand',
                               spreadsheet_id='1bz0JRZABFCk54ZswUo85j_KY8Hn_9uYj-GnqTfif4vA',
                               datasource='Neo4J',
                               persistent_column='E'
                               )

        self.report.result_query = """
            // Actieve Asset met tegengestelde AIMtoestand.
            // https://wegenenverkeer.data.vlaanderen.be/doc/conceptscheme/KlAIMToestand?rel=top-concept
            // Toegestane waardes voor AIMToestand: in-gebruik, uit-gebruik, overgedragen, in-opbouw, null
            // Niet-toegestande waardes voor AIMToestand: verwijderd, geannuleerd, in-ontwerp, gepland
            MATCH (asset:Asset {isActief: True})
            WHERE asset.toestand in ['verwijderd', 'geannuleerd', 'in-ontwerp', 'gepland'] 
            RETURN asset.uuid as uuid, asset.type as assettype,  asset.isActief as isActief, asset.toestand as AIMToestand
            ORDER BY asset.type, asset.toestand
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
