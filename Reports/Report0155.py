from DQReport import DQReport


class Report0155:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0155',
                               title='LS/HS met Voedingsrelatie anders dan LS-Deel/HS-Deel',
                               spreadsheet_id='19jhMsSzcxBHTjveVWMJWXRlKxYKlw1r0m5j5JSMfJ4k',
                               datasource='Neo4J',
                               persistent_column='K'
                               )

        self.report.result_query = """
        // Obtain all LS and HS nodes with Voeding relationship to nodes that are not LSDeel or HSDeel respectively
        MATCH (n)-[r:Voedt]-(other)
        WHERE 
            n.isActief = true AND
            (n:LS AND NOT other:LSDeel) OR
            (n:HS AND NOT other:HSDeel)
        RETURN
            n.uuid as uuid
            , n.typeURI as typeURI
            , n.naampad as naampad
            , n.naam as naam
            , n.isActief as isActief
            , other.uuid AS asset2_uuid
            , other.typeURI as asset2_typeURI
            , other.naampad AS asset2_naampad
            , other.naam as asset2_naam
            , other.isActief as asset2_isActief
        ORDER BY other.typeURI asc
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
