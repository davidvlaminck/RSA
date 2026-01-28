from DQReport import DQReport


class Report0119:
    def __init__(self):
        self.report = None

    def init_report(self):
n 1        aql_query = """
LET dnblaagspanning_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#DNBLaagspanning" LIMIT 1 RETURN at._key)
LET dnbhoogspanning_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#DNBHoogspanning" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.assettype_key IN [dnbhoogspanning_key, dnblaagspanning_key]

  FOR b, r IN 1..1 OUTBOUND a._id betrokkenerelaties
    FILTER r.rol != "installatieverantwoordelijke"
    RETURN {
      uuid: a._key,
      naam: a.AIMNaamObject_naam,
      typeURI: a['@type'],
      relatie_rol: r.rol,
      agent_naam: b ? b.purl.Agent_naam : null
    }
"""
        self.report = DQReport(name='report0119',
                               title='DNBHoogspanning en DNBLaagspanning hebben een installatieverantwoordelijke',
                               spreadsheet_id='1hGwws9A8U8F5dQZChGNDH4YOtiuB8LVq7Ovh93DmD2c',
                               datasource='ArangoDB',
                               persistent_column='F')

        self.report.result_query = aql_query
        self.report.cypher_query = """
                MATCH (a:DNBHoogspanning|DNBLaagspanning {isActief:TRUE})-[r:HeeftBetrokkene]->(b:Agent)
                WHERE r.rol <> 'installatieverantwoordelijke'
                RETURN a.uuid, a.naam, a.typeURI, r.rol as relatie_rol, b.naam as agent_naam
                
                """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
