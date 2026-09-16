from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0059(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET ups_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#UPS" LIMIT 1 RETURN at._key)
LET maxDepth = 4

FOR x IN (
  FOR e IN voedt_relaties
    COLLECT from_id = e._from
    FOR a IN assets
      FILTER a._id == from_id
      FILTER a.AIMDBStatus_isActief == true
      FILTER a.assettype_key != ups_key
      RETURN a
)
  FOR v, e, p IN 1..maxDepth OUTBOUND x voedt_relaties
    OPTIONS { order: "bfs", uniqueVertices: "none", uniqueEdges: "path" }

    FILTER v.assettype_key != ups_key
    FILTER v._id == x._id
    FILTER LENGTH(p.edges) > 1

    LET loopVertices = p.vertices

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
                               persistent_column='F',
                               excel_filename='[RSA] Assets met lussen in voeding.xlsx',)

        self.report.result_query = aql_query

        self.report.cypher_query = """
            MATCH p=(x:Asset {isActief: True})-[:Voedt*]->(x)
            WHERE all(n in nodes(p) WHERE NOT (n:UPSLegacy))
            WITH x, reduce(path_loop = [], n IN nodes(p) | path_loop + [[n.uuid, n.typeURI]]) as path_loop
            RETURN DISTINCT x.uuid AS uuid, x.naampad AS naampad, x.typeURI AS typeURI, x.toestand as toestand, path_loop
        """
    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
