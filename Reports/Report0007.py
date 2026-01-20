from DQReport import DQReport


class Report0007:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0007',
                               title='Camera\'s hebben een Sturing relatie met een Netwerkpoort of Omvormer',
                               spreadsheet_id='1NKB8J6is9xTrIrDcZAP_IraBqs65JhTpoCLDMaT881A',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (c:Camera {isActief:TRUE}) 
        WHERE NOT EXISTS ((c)-[:Sturing]-(:onderdeel :Netwerkpoort {isActief:TRUE})) AND NOT EXISTS ((c)-[:Sturing]-(:onderdeel :Omvormer {isActief:TRUE}))
        WITH c
        OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN c.uuid, c.naam, a.naam as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)


aql_query = """
LET camera_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Camera" LIMIT 1 RETURN at._key)
LET netwerkpoort_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET omvormer_key     = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Omvormer" LIMIT 1 RETURN at._key)

FOR c IN assets
  FILTER c.assettype_key == camera_key
  FILTER c.AIMDBStatus_isActief == true

  // no Sturing to Netwerkpoort
  LET has_np = LENGTH(
    FOR o, rel IN ANY c sturing_relaties
      FILTER o.assettype_key == netwerkpoort_key
      LIMIT 1
      RETURN 1
  ) > 0

  // no Sturing to Omvormer
  LET has_omvormer = LENGTH(
    FOR o, rel IN ANY c sturing_relaties
      FILTER o.assettype_key == omvormer_key
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_np AND NOT has_omvormer

  // OPTIONAL toezichter via betrokkenerelaties
  LET toezichter = FIRST(
    FOR v, e IN 1..1 OUTBOUND c._id betrokkenerelaties
      FILTER e.rol == "toezichter"
      RETURN v
  )

  RETURN {
    uuid:       c._key,
    naam:       c.AIMNaamObject_naam,
    toezichter: toezichter ? toezichter.purl.Agent_naam : null
  }
"""

