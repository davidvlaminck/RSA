from DQReport import DQReport


class Report0114:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0114',
                               title='EAN Nummer niet als commentaar gedocumenteerd',
                               spreadsheet_id='188xxFUa1uZ8GPgwB9a2c0gtkrdtacg5ft5TkODanatk',
                               datasource='Neo4J',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
        // Find active assets whose note contains an EAN (18 digits starting with 54)
        MATCH (a {isActief: true})
        WHERE a.notitie =~ '.*54\\d{16}.*'
          AND a.typeURI <> 'https://lgc.data.wegenenverkeer.be/ns/installatie#SeinbrugRR'
          
        // Explore possible connection paths to DNB nodes
        OPTIONAL MATCH path = (a)
          -[:Voedt*0..5]-
          (:Asset)
          -[:HoortBij]-
          (b:DNBHoogspanning|DNBLaagspanning)
        
        RETURN 
          a.uuid AS uuid,
          a.naampad AS naampad,
          a.typeURI AS typeURI,
          a.isActief AS isActief,
          a.toestand AS toestand,
          a.notitie AS commentaar,
          b.eanNummer AS eanNummer_bijhorendeAsset,
          a.`tz:toezichter.tz:voornaam`,
          a.`tz:toezichter.tz:naam`,
          a.`tz:toezichter.tz:email`
        ORDER BY 
          typeURI, uuid
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
