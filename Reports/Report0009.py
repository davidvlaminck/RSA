from DQReport import DQReport


class Report0009:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0009',
                               title='Omvormers hebben een Bevestiging relatie met een Behuizing',
                               spreadsheet_id='1A4kata3Eg9fMjsUE8Za5XEtcF7JEm_-IftHhGz6SnJo',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """MATCH (o:Omvormer {isActief:TRUE})
        WHERE NOT EXISTS ((o)-[:Bevestiging]-(:Wegkantkast {isActief:TRUE})) AND NOT EXISTS ((o)-[:Bevestiging]-(:Montagekast {isActief:TRUE}))
        WITH o
        OPTIONAL MATCH (o)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        OPTIONAL MATCH (o)-[:Bevestiging]->(b:onderdeel {isActief:TRUE})
        RETURN o.uuid, o.naam, a.naam as toezichter, b.typeURI as behuizing_type"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET omvormer_key    = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Omvormer"    LIMIT 1 RETURN at._key)
LET wegkantkast_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Wegkantkast" LIMIT 1 RETURN at._key)
LET montagekast_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Montagekast" LIMIT 1 RETURN at._key)
LET bevestiging_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "Bevestiging"            LIMIT 1 RETURN rt._key)

FOR o IN assets
  FILTER
    o.assettype_key == omvormer_key
    AND o.AIMDBStatus_isActief == true

  // no Bevestiging with Wegkantkast
  LET has_wegkantkast = LENGTH(
    FOR k, rel IN ANY o assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND k.assettype_key == wegkantkast_key
        AND k.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  // no Bevestiging with Montagekast
  LET has_montagekast = LENGTH(
    FOR k, rel IN ANY o assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND k.assettype_key == montagekast_key
        AND k.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_wegkantkast AND NOT has_montagekast

  // OPTIONAL toezichter via betrokkenerelaties
  LET toezichter = FIRST(
    FOR v, e IN 1..1 OUTBOUND o._id betrokkenerelaties
      FILTER e.rol == "toezichter"
      RETURN v
  )

  // OPTIONAL Bevestiging -> any actief onderdeel as behuizing
  LET behuizing = FIRST(
    FOR b, rel IN OUTBOUND o assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND b.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN b
  )

  RETURN {
    uuid:           o._key,
    naam:           o.AIMNaamObject_naam,
    toezichter:     toezichter ? toezichter.purl.Agent_naam : null,
    behuizing_type: behuizing ? behuizing.typeURI : null
  }
"""