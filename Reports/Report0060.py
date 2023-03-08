from DQReport import DQReport


class Report0060:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0060',
                               title='Er zijn geen conflicten tussen EAN-nummers (dubbel EAN-nummer).',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='G')

        self.report.result_query = """
            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) 
            WHERE ((y:DNBHoogspanning) OR (y:DNBLaagspanning)) AND  x.eanNummer <> y.eanNummer
            RETURN 
                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, 
                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,
                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie
            UNION 
            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) 
            WHERE (y:DNBHoogspanning) OR (y:DNBLaagspanning)
            WITH x, count(DISTINCT y.eanNummer) as ean_count 
            WHERE ean_count > 1
            RETURN 
                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, 
                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,
                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
