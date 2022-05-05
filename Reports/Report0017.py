from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")
    r = DQReport(name='report0017',
                 title='Netwerkkaarten hebben een Bevestiging relatie met een Netwerkelement',
                 spreadsheet_id='1UfYhxcM0z8uq9-GwfDJhHNVpuhoWtUprrPGMfPSXeGk',
                 datasource='Neo4J',
                 persistent_column='F')

    # query that fetches uuids of results
    result_query = """OPTIONAL MATCH (n:Netwerkkaart {isActief:TRUE})-[r:Bevestiging]-(o {isActief:TRUE})
WHERE r IS NULL OR (r IS NOT NULL AND NOT (o:Netwerkelement))
RETURN n.uuid AS kaart_uuid, n.naam AS kaart_naam, o.uuid AS niet_netwerk_uuid, o.naam AS niet_netwerk_naam, o.typeURI"""

    r.result_query = result_query
    r.run_report()


