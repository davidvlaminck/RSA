from DQReport import DQReport


class Report0034:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0034',
                               title="NNI Netwerkpoorten hebben een Sturing relatie met een NNI Netwerkpoort",
                               spreadsheet_id='1Q0ypijGhIMmax4iR3DHHu4FMYVbkU_LCQhBAyzbIA2k',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})-[:Bevestiging]-(:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) 
        WHERE NOT EXISTS ((n)-[:Sturing]-(:Netwerkpoort {isActief:TRUE, type:'NNI'}))
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET netwerkpoort_key    = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET netwerkelement_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)
LET bevestiging_key     = FIRST(FOR rt IN relatietypes FILTER rt.short == "Bevestiging" LIMIT 1 RETURN rt._key)
LET sturing_key         = FIRST(FOR rt IN relatietypes FILTER rt.short == "Sturing" LIMIT 1 RETURN rt._key)

FOR n IN assets
  FILTER
    n.assettype_key == netwerkpoort_key
    AND n.AIMDBStatus_isActief == true
    AND n.Netwerkpoort_type == "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkpoortType/NNI"

  // Check Bevestiging to Netwerkelement with gebruik 'l2-switch'
  LET l2_switch = FIRST(
    FOR e, rel IN ANY n assetrelaties
      FILTER
        rel.relatietype_key == bevestiging_key
        AND e.assettype_key == netwerkelement_key
        AND e.AIMDBStatus_isActief == true
        AND e.Netwerkelement_gebruik == "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkelemGebruik/l2-switch"
      LIMIT 1
      RETURN e
  )
  FILTER l2_switch != null

  // Check absence of Sturing to another NNI Netwerkpoort
  LET nni_sturing = FIRST(
    FOR np, rel IN ANY n assetrelaties
      FILTER
        rel.relatietype_key == sturing_key
        AND np.assettype_key == netwerkpoort_key
        AND np.AIMDBStatus_isActief == true
        AND np.Netwerkpoort_type == "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkpoortType/NNI"
      LIMIT 1
      RETURN np
  )
  FILTER nni_sturing == null

  RETURN {
    uuid: n._key,
    naam: n.AIMNaamObject_naam
  }
"""