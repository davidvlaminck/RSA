from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")
    r = DQReport(name='report0016',
                 title='Netwerkpoorten hebben een Bevestiging relatie met een Netwerkelement of een Netwerkkaart',
                 spreadsheet_id='16NJCwhrHnYuz6Z9leqGswfOR0bt7EdBK_GonPB-3y7o',
                 datasource='Neo4J',
                 persistent_column='F')

    # query that fetches uuids of results
    result_query = """OPTIONAL MATCH (n:Netwerkpoort {isActief:TRUE})-[r:Bevestiging]-(o {isActief:TRUE})
WHERE r IS NULL OR (r IS NOT NULL AND NOT (o:Netwerkkaart or o:Netwerkelement))
RETURN n.uuid AS poort_uuid, n.naam AS poort_naam, o.uuid AS niet_netwerk_uuid, o.naam AS niet_netwerk_naam, o.typeURI"""

    r.result_query = result_query
    r.run_report()


