from DQReport import DQReport


class Report0032:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0032',
                               title="Netwerkpoorten hebben een type",
                               spreadsheet_id='1CNSGgZbARVwRzrMB5a2LrSz-HJblvzAGWODsPOFE1jo',
                               datasource='Neo4J',
                               persistent_column='C')

        self.report.result_query = """MATCH (n:Netwerkpoort {isActief:TRUE})-[:Bevestiging]-(e:Netwerkelement {isActief:TRUE})
        WHERE NOT e.merk IN ['NOKIA', 'Ciena']
        WITH n
        WHERE n.type IS NULL 
        RETURN n.uuid, n.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# aql_query = """
# FOR n IN assets
#   FILTER n.assettype_key == "6b3dba37"
#     AND n.AIMDBStatus_isActief == TRUE
#
#   FOR v, rel IN ANY n assetrelaties
#     FILTER rel.relatietype_key == "3ff9"
#       AND v.assettype_key == "b6f86b8d"
#       AND v.AIMDBStatus_isActief == TRUE
#       AND !v.Netwerkelement_merk IN ["https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/NOKIA",
#         "https://wegenenverkeer.data.vlaanderen.be/id/concept/KlNetwerkMerk/Ciena"]
#
#   FILTER n.Netwerkpoort_type == null
#   RETURN { uuid: n._key, naam: n.AIMNaamObject_naam }
# """