from DQReport import DQReport


class Report0059:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0059',
                               title='Er zijn geen assets die zichzelf direct of indirect voeden (geen lussen in voeding).',
                               spreadsheet_id='15z-3mTVmjg63EepO1uaN5R5dgFARcfiyrRBbXa3TzUQ',
                               datasource='Neo4J',
                               persistent_column='F')

        self.report.result_query = """
            MATCH p=(x:Asset {isActief: True})-[:Voedt*]->(x)
            WHERE all(n in nodes(p) WHERE NOT (n:UPSLegacy))
            WITH x, reduce(path_loop = [], n IN nodes(p) | path_loop + [[n.uuid, n.typeURI]]) as path_loop
            RETURN DISTINCT x.uuid AS uuid, x.naampad AS naampad, x.typeURI AS typeURI, x.toestand as toestand, path_loop
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)


# to verify
aql_query = """
LET voedt_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "Voedt" LIMIT 1 RETURN rt._key)
LET upsl_key  = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#UPSLegacy" LIMIT 1 RETURN at._key)

FOR x IN assets
  FILTER x.AIMDBStatus_isActief == true

  FOR v, e, p IN 1..10 OUTBOUND x assetrelaties
    OPTIONS { order: "bfs", uniqueVertices: "global", uniqueVertices: "path" }
    FILTER e.relatietype_key == voedt_key
    FILTER v._id == x._id
      AND (
          FOR n IN p.vertices
            FILTER n.assettype_key == upsl_key
            LIMIT 1
            RETURN 1
        ) == []
    
    LET path_loop = (
      FOR n IN p.vertices
        RETURN [n._key, n.typeURI]
    )

    RETURN DISTINCT {
      uuid: x._key,
      naampad: x.AIMNaamObject_naampad,
      typeURI: x.typeURI,
      toestand: x.toestand,
      path_loop: path_loop
    }

"""