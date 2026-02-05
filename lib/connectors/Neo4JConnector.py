from neo4j import GraphDatabase


class Neo4JConnector:
    def __init__(self, uri: str = '', user: str = '', password: str = '', database: str = 'neo4j'):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.db = database

    def perform_query(self, query, **kwargs):
        with self.driver.session(database=self.db) as session:
            return session.run(query, **kwargs)


class SingleNeo4JConnector:
    _instance = None

    @classmethod
    def init(cls, uri: str = '', user: str = '', password: str = '', database: str = 'neo4j'):
        cls._instance = Neo4JConnector(uri, user, password, database)

    @classmethod
    def get_connector(cls):
        if cls._instance is None:
            raise RuntimeError('Run SingleNeo4JConnector.init(...) before calling get_connector')
        return cls._instance
