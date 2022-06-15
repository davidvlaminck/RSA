from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

    r = DQReport(name='report0031',
                 title="Netwerkementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
                 spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (n:Netwerkelement) 
WHERE n.isActief = TRUE AND n.gebruik = 'l2-switch' AND NOT EXISTS ((n)-[:HoortBij]->(:L2AccessStructuur {isActief:TRUE}))
RETURN n.uuid, n.naam"""

    r.result_query = result_query
    r.run_report()
