from DQReport import DQReport


class Report0032:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
FOR n IN assets
  FILTER n.assettype_key == "6b3dba37"
  FILTER n.AIMDBStatus_isActief == TRUE
  FILTER n.Netwerkpoort_type == null

  FOR v, rel IN ANY n bevestiging_relaties
    FILTER v.assettype_key == "b6f86b8d"
    FILTER v.Netwerkelement_merk NOT IN [
      "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NOKIA",
      "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/Ciena"
    ]

    RETURN { uuid: n._key, naam: n.AIMNaamObject_naam }
"""
        self.report = DQReport(name='report0032',
                               title="Netwerkpoorten hebben een type",
                               spreadsheet_id='1CNSGgZbARVwRzrMB5a2LrSz-HJblvzAGWODsPOFE1jo',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (n:Netwerkpoort {isActief:TRUE})-[:Bevestiging]-(e:Netwerkelement {isActief:TRUE})
        WHERE NOT e.merk IN ['NOKIA', 'Ciena']
        WITH n
        WHERE n.type IS NULL 
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
