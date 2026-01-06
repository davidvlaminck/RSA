from DQReport import DQReport


class Report0010:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0010',
                               title='Camera\'s zijn het doel van een Voedt relatie met een Stroomkring of PoEInjector',
                               spreadsheet_id='1MzUeaGLeqV78IMBuTTFoM47y4nXja993AZnZF21Zu2U',
                               datasource='Neo4J',
                               persistent_column='D')

        # query that fetches uuids of results
        self.report.result_query = """MATCH (c:Camera {isActief:TRUE})
        WHERE NOT EXISTS ((c)<-[:Voedt]-(:Stroomkring {isActief:TRUE})) AND NOT EXISTS ((c)<-[:Voedt]-(:PoEInjector {isActief:TRUE}))
        WITH c
        OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
        RETURN c.uuid, c.naam, a.naam as toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET camera_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Camera"      LIMIT 1 RETURN at._key)
LET stroomkring_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Stroomkring" LIMIT 1 RETURN at._key)
LET poe_injector_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#PoEInjector" LIMIT 1 RETURN at._key)
LET voedt_key        = FIRST(FOR rt IN relatietypes FILTER rt.short == "Voedt"                   LIMIT 1 RETURN rt._key)

FOR c IN assets
  FILTER
    c.assettype_key == camera_key
    AND c.AIMDBStatus_isActief == true

  // no INBOUND Voedt from Stroomkring
  LET has_stroomkring = LENGTH(
    FOR s, rel IN INBOUND c assetrelaties
      FILTER
        rel.relatietype_key == voedt_key
        AND s.assettype_key == stroomkring_key
        AND s.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  // no INBOUND Voedt from PoEInjector
  LET has_poe = LENGTH(
    FOR p, rel IN INBOUND c assetrelaties
      FILTER
        rel.relatietype_key == voedt_key
        AND p.assettype_key == poe_injector_key
        AND p.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_stroomkring AND NOT has_poe

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