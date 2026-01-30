from DQReport import DQReport


class Report0059:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET ups_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#UPS" LIMIT 1 RETURN at._key)
LET maxDepth = 10

FOR x IN assets
  FILTER x != null
  FILTER x.AIMDBStatus_isActief == true

  FOR v, e, p IN 1..maxDepth OUTBOUND x voedt_relaties
    OPTIONS { order: "bfs", uniqueVertices: "global" }

    LET back = FIRST(
      FOR be IN voedt_relaties
        FILTER be._from == v._id
        FILTER be._to == x._id
        LIMIT 1
        RETURN be
    )
    FILTER back != null

    LET loopVertices = APPEND(p.vertices, [x])

    FILTER LENGTH(
      FOR n IN loopVertices
        FILTER n.assettype_key == ups_key
        LIMIT 1
        RETURN 1
    ) == 0

    LET path_loop = (FOR n IN loopVertices RETURN [n._key, n["@type"]])

    RETURN DISTINCT {
      uuid: x._key,
      naampad: x.AIMNaamObject_naampad,
      typeURI: x["@type"],
      toestand: x.toestand,
      path_loop: path_loop
    }
"""
        self.report = DQReport(name='report0059',
                               title='Er zijn geen assets die zichzelf direct of indirect voeden (geen lussen in voeding).',
                               spreadsheet_id='15z-3mTVmjg63EepO1uaN5R5dgFARcfiyrRBbXa3TzUQ',
                               datasource='ArangoDB',
                               persistent_column='F')

        self.report.result_query = aql_query
        self.report.cypher_query = """
            MATCH p=(x:Asset {isActief: True})-[:Voedt*]->(x)
            WHERE all(n in nodes(p) WHERE NOT (n:UPSLegacy))
            WITH x, reduce(path_loop = [], n IN nodes(p) | path_loop + [[n.uuid, n.typeURI]]) as path_loop
            RETURN DISTINCT x.uuid AS uuid, x.naampad AS naampad, x.typeURI AS typeURI, x.toestand as toestand, path_loop
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
