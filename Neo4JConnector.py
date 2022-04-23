from neo4j import GraphDatabase


class Neo4JConnector:
    def __init__(self, uri: str = '', user: str = '', password: str = ''):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def perform_query(self, query, **kwargs):
        session = self.driver.session()
        result = session.run(query=query, parameters=None, kwparameters=kwargs)
        return result


class SingleNeo4JConnector:
    neo4j_connector: Neo4JConnector | bool = None

    @classmethod
    def init(cls, uri: str = '', user: str = '', password: str = ''):
        cls.neo4j_connector = Neo4JConnector(uri, user, password)

    @classmethod
    def get_connector(cls) -> Neo4JConnector:
        if cls.neo4j_connector is None:
            raise RuntimeError('Run the init method of this class first')
        return cls.neo4j_connector
