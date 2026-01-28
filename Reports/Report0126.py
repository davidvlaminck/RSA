from DQReport import DQReport


class Report0126:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET kabelnetbuis_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#KabelnetBuis"   LIMIT 1 RETURN at._key)
LET beschermbuis_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Beschermbuis"  LIMIT 1 RETURN at._key)
LET heeftnetwerktoegang_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "HeeftNetwerktoegang" LIMIT 1 RETURN rt._key)

FOR n IN assets
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.assettype_key == kabelnetbuis_key
  FOR m, r IN ANY n assetrelaties
    FILTER r.AIMDBStatus_isActief == true
    FILTER r.relatietype_key != heeftnetwerktoegang_key
    FILTER m.AIMDBStatus_isActief == true
    FILTER m.assettype_key == beschermbuis_key
    RETURN {
      uuid: n._key,
      toestand: n.toestand,
      isActief: n.AIMDBStatus_isActief
    }
"""
        self.report = DQReport(name='report0126',
                               title='KabelnetBuis HeeftNetwerktoegang tot een BeschermBuis',
                               spreadsheet_id='1_U31z99SVb2B_BbiXd9ZEB-tmwI4KYM17amUYWinkN0',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """
        // KabelnetBuis HeeftNetwerktoegang tot een BeschermBuis
        MATCH (n:KabelnetBuis {isActief:true})-[r {isActief:TRUE}]-(m:Beschermbuis {isActief:TRUE})
        WHERE r.type <> 'HeeftNetwerktoegang'
        RETURN n.uuid as uuid, n.toestand as toestand, n.isActief as isActief
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
