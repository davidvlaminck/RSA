from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

    r = DQReport(name='report0030',
                 title='Netwerkelementen hebben een (afgeleide) locatie',
                 spreadsheet_id='1ZAZ8chzMbLEyGd-cbZM6S7Uw4aNOrBmAE1KWnbyvdK4',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (n:Netwerkelement {isActief:TRUE})
WHERE n.geometry IS NULL
RETURN n.uuid, n.naam"""

    r.result_query = result_query
    r.run_report()
