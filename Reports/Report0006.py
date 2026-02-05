from lib.reports.DQReport import DQReport


class Report0006:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET wegkantkast_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Wegkantkast\" LIMIT 1 RETURN at._key)
LET kast_key        = FIRST(FOR at IN assettypes FILTER at.short_uri == \"onderdeel#Kast\"        LIMIT 1 RETURN at._key)


FOR a IN assets
  FILTER a.assettype_key == wegkantkast_key
  FILTER a.AIMDBStatus_isActief == true

  LET kast = FIRST(
    FOR k, rel IN OUTBOUND a hoortbij_relaties
      FILTER k.assettype_key == kast_key
      LIMIT 1
      RETURN k
  )
  FILTER kast == null

  RETURN {
    uuid: a._key,
    naam: a.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0006',
                               title='Wegkantkasten hebben een HoortBij relatie naar Kast objecten',
                               spreadsheet_id='1_yLv--qorkqbx5ym_qBUTxc6b7mOvdm5kD8SrWPkB5I',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (a:Asset :Wegkantkast {isActief:TRUE}) \n        WHERE NOT EXISTS ((a)-[:HoortBij]->(:Kast {isActief:TRUE}))\n        RETURN a.uuid, a.naam"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
