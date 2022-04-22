from neo4j import GraphDatabase


class Neo4JConnector:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def perform_query(self, query, **kwargs):
        session = self.driver.session()
        result = session.run(query=query, parameters=None, kwparameters=kwargs)
        return result
