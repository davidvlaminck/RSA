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


# AQL equivalent (documentation / future migration)
# Cypher:
# MATCH (n)-[r:Voedt]-(other)
# WHERE n.isActief = true AND ((n:LS AND NOT other:LSDeel) OR (n:HS AND NOT other:HSDeel))
# RETURN n..., other...

aql_query = """
LET ls_key     = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#LS"            LIMIT 1 RETURN at._key)
LET hs_key     = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#HS"            LIMIT 1 RETURN at._key)
LET lsdeel_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#LSDeel"        LIMIT 1 RETURN at._key)
LET hsdeel_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#HSDeel"        LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.assettype_key IN [ls_key, hs_key]

  FOR other, rel IN ANY n voedt_relaties

    FILTER (
      (n.assettype_key == ls_key AND other.assettype_key != lsdeel_key)
      OR
      (n.assettype_key == hs_key AND other.assettype_key != hsdeel_key)
    )

    SORT other['@type'] ASC

    RETURN {
      uuid: n._key,
      typeURI: n['@type'],
      naampad: n.NaampadObject_naampad,
      naam: n.AIMNaamObject_naam,
      isActief: n.AIMDBStatus_isActief,
      asset2_uuid: other._key,
      asset2_typeURI: other['@type'],
      asset2_naampad: other.NaampadObject_naampad,
      asset2_naam: other.AIMNaamObject_naam,
      asset2_isActief: other.AIMDBStatus_isActief
    }
"""
