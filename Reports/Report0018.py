from DQReport import DQReport

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper

if __name__ == '__main__':
    SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                             readonly_scope=False)
    SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")
    r = DQReport(name='report0018',
                 title='Linken zijn het doel van exact 2 HoortBij relaties komende van Netwerkpoorten',
                 spreadsheet_id='1U_27rorzzxcoBOxLoHIN8Vt20idDafrb5DGE_ECWVAw',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (gl:Link {isActief:TRUE})<-[:HoortBij]-(p:Netwerkpoort {isActief:TRUE})
WITH gl, COUNT(p) AS aantal_poorten
WHERE aantal_poorten = 2
WITH collect(gl.uuid) AS good_links
MATCH (l:Link {isActief:TRUE} )
WHERE NOT l.uuid IN good_links
RETURN l.uuid, l.naam"""

    r.result_query = result_query
    r.run_report()


