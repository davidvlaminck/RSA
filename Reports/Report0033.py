from DQReport import DQReport
from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

    r = DQReport(name='report0032',
                 title="Netwerkpoorten met type 'UNI' hebben een hoortbij relatie naar installatie VLAN",
                 spreadsheet_id='14ecrURzs2O61GsGpiFvd85MuwX-A69gbh6tP37X3idQ',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (n:Netwerkpoort {isActief:TRUE, type:'UNI'}) 
WHERE NOT EXISTS ((n)-[:HoortBij]->(:VLAN {isActief:TRUE})) 
RETURN n.uuid, n.naam"""

    r.result_query = result_query
    r.run_report()
