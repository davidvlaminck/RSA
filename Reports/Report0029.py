from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

    r = DQReport(name='report0029',
                 title='IP elementen hebben HoortBij relatie met een Netwerkelement',
                 spreadsheet_id='1VJmqHesEfOaZzYD8rZdZUNeKUoCBKMetgltL74bX9jk',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """OPTIONAL MATCH (i:IP {isActief:TRUE})<-[h:HoortBij]-(n:Netwerkelement {isActief:TRUE})
WHERE i.`tz:toezichtgroep.tz:naam` = 'EMT_TELE' AND (h IS NULL OR n IS NULL)
RETURN i.uuid, i.naampad"""

    r.result_query = result_query
    r.run_report()
