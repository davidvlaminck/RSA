from DQReport import DQReport


class Report0046:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0046',
                               title='Een Onderbouw heeft steeds een ligtOp relatie naar een Geotextiel',
                               spreadsheet_id='1eFVzTiSiPASlvTE4tva9Vw1on5Z8AJNalj4im8tRops',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """
            MATCH (o:Onderbouw {isActief: TRUE})
            WHERE NOT EXISTS((o)-[:LigtOp]->(:Geotextiel {isActief: TRUE}))
            RETURN o.uuid as uuid, o.toestand as toestand
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET onderbouw_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Onderbouw" LIMIT 1 RETURN at._key)
LET geotextiel_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Geotextiel" LIMIT 1 RETURN at._key)
LET ligtop_key     = FIRST(FOR rt IN relatietypes FILTER rt.short == "LigtOp" LIMIT 1 RETURN rt._key)

FOR o IN assets
  FILTER
    o.assettype_key            == onderbouw_key
    AND o.AIMDBStatus_isActief == true

  LET geotextiel = FIRST(
    FOR g, rel IN OUTBOUND o assetrelaties
      FILTER
        rel.relatietype_key == ligtop_key
        AND g.assettype_key == geotextiel_key
        AND g.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN g
  )
  FILTER geotextiel == null

  RETURN {
    uuid: o._key,
    toestand: o.toestand
  }
"""
