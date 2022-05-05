from DQReport import DQReport
from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

    r = DQReport(name='report0015',
                 title='Camera\'s hebben een unieke naam',
                 spreadsheet_id='1GM6mBwfsLkEELjroSw-df6A2HXSQnOFAeudUzTybMQE',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (a:Camera {isActief:TRUE})
WITH a.naam AS naam, COUNT(a.naam) AS aantal
WHERE aantal > 1
MATCH (b:Camera {isActief:TRUE naam:naam})
RETURN b.uuid, b.naam"""

    r.result_query = result_query
    r.run_report()
    

