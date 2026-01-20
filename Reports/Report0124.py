from DQReport import DQReport


class Report0124:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0124',
                               title='KabelnetToegang HeeftNetwerktoegang tot een Behuizing',
                               spreadsheet_id='1Fia3N3bXG7LXBSbcst7jDM5N8Lr9HXHc3eCVcgNIdrM',
                               datasource='Neo4J',
                               persistent_column='D'
                               )

        self.report.result_query = """
        // KabelnetToegang heeft een relatie "heeftNetwerktoegang" naar een asset van het type behuizing (gebouw, lokaal, indoorkast, cabine, wegkantkast, technischePut, montagekast). De status van beide assets en de relatie tussen beide is actief.
        MATCH (n:KabelnetToegang {isActief:True})-[r {isActief:TRUE}]-(m:Gebouw|Lokaal|IndoorKast|Cabine|Kast|IndoorKast|Wegkantkast|Montagekast|Hulppostkast|TechnischePut {isActief:True})
        WHERE r.type <> "HeeftNetwerktoegang"
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


# AQL equivalent (documentation / future migration)
# Cypher:
# MATCH (n:KabelnetToegang {isActief:True})-[r {isActief:TRUE}]-(m:Gebouw|Lokaal|IndoorKast|Cabine|Kast|Wegkantkast|Montagekast|Hulppostkast|TechnischePut {isActief:True})
# WHERE r.type <> "HeeftNetwerktoegang"
# RETURN n.uuid, n.toestand, n.isActief

aql_query = """
LET kabelnettoegang_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#KabelnetToegang" LIMIT 1 RETURN at._key)

LET behuizing_keys = (
  FOR at IN assettypes
    FILTER at.short_uri IN [
      "installatie#Gebouw",
      "installatie#Lokaal",
      "onderdeel#HSCabine",
      "onderdeel#IndoorKast",
      "onderdeel#Wegkantkast",
      "onderdeel#Montagekast",
      "onderdeel#Hulppostkast",
      "onderdeel#TechnischePut"
    ]
    RETURN at._key
)

FOR n IN assets
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.assettype_key == kabelnettoegang_key

  FOR m, r IN ANY n assetrelaties
    FILTER r.AIMDBStatus_isActief == true
    FILTER m.AIMDBStatus_isActief == true
    FILTER m.assettype_key IN behuizing_keys

    // In Arango we typically compare by relatietype_key; Cypher used r.type.
    // Keep the same semantics: flag relations that are NOT of type 'HeeftNetwerktoegang'.
    LET is_heeftnetwerktoegang = LENGTH(
      FOR rt IN relatietypes
        FILTER rt._key == r.relatietype_key
        FILTER rt.short == "HeeftNetwerktoegang"
        LIMIT 1
        RETURN 1
    ) > 0

    FILTER NOT is_heeftnetwerktoegang

    RETURN {
      uuid: n._key,
      toestand: n.toestand,
      isActief: n.AIMDBStatus_isActief
    }
"""
