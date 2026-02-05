from lib.reports.DQReport import DQReport


class Report0100:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET verkeersregelaar_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Verkeersregelaar" LIMIT 1 RETURN at._key)
LET tlcfipoort_key       = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#TLCfiPoort"       LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.assettype_key == verkeersregelaar_key

  // Use derived Sturing-only edges between active assets (see fill_sturing_relaties -> sturing_relaties).
  // Cypher used an undirected pattern: (a)-[:Sturing]-(:TLCfiPoort)
  // So we use ANY here (both INBOUND and OUTBOUND).
  LET has_sturing_to_tlc = LENGTH(
    FOR v, rel IN ANY a sturing_relaties
      FILTER v.assettype_key == tlcfipoort_key
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_sturing_to_tlc

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0100',
                               title='Verkeersregelaars hebben een sturingsrelatie naar een TLCfiPoort',
                               spreadsheet_id='1MLoe5_exhht_bR2y9uTxPBaGIAObzwUqqHvWwBttRzk',
                               datasource='ArangoDB',
                               persistent_column='C',
                               link_type='eminfra')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Verkeersregelaar {isActief:TRUE}) \n        WHERE NOT EXISTS ((a)-[:Sturing]-(:TLCfiPoort {isActief:TRUE}))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
