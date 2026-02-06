from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0034(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET netwerkpoort_key     = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Netwerkpoort\" LIMIT 1 RETURN at._key)
LET netwerkelement_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Netwerkelement\" LIMIT 1 RETURN at._key)

FOR n IN assets
  FILTER n.assettype_key == netwerkpoort_key
  FILTER n.AIMDBStatus_isActief == true
  FILTER n.Netwerkpoort_type == \"https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkpoortType/NNI\"

  // Check Bevestiging to Netwerkelement with gebruik 'l2-switch'
  LET l2_switch = FIRST(
    FOR e, rel IN ANY n bevestiging_relaties
      FILTER e.assettype_key == netwerkelement_key
      FILTER e.Netwerkelement_gebruik == \"https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkelemGebruik/l2-switch\"
      LIMIT 1
      RETURN e
  )
  FILTER l2_switch != null

  // Check absence of Sturing to another NNI Netwerkpoort
  LET nni_sturing = FIRST(
    FOR np, rel IN ANY n sturing_relaties
      FILTER np.assettype_key == netwerkpoort_key
      FILTER np.Netwerkpoort_type == \"https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkpoortType/NNI\"
      LIMIT 1
      RETURN np
  )
  FILTER nni_sturing == null

  RETURN {
    uuid: n._key,
    naam: n.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0034',
                               title="NNI Netwerkpoorten hebben een Sturing relatie met een NNI Netwerkpoort",
                               spreadsheet_id='1Q0ypijGhIMmax4iR3DHHu4FMYVbkU_LCQhBAyzbIA2k',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'NNI'})-[:Bevestiging]-(:Netwerkelement {isActief:TRUE, gebruik:'l2-switch'}) \n        WHERE NOT EXISTS ((n)-[:Sturing]-(:Netwerkpoort {isActief:TRUE, type:'NNI'}))\n        RETURN n.uuid, n.naam"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
