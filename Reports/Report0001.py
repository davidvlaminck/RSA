from DQReport import DQReport


r = DQReport(name='report0001',
             title='Onderdelen hebben een HoortBij relatie',
             spreadsheet_id='16iUSRuS9M85P4E7Mi5-1J8pWgPr6Ehp1liEmRaZFNi4',
             datasource='Neo4J',
             persistent_column='D')

# query that fetches uuids of results
result_query = """MATCH (pk:Asset)-[:Bevestiging]-(e:Asset {typeURI:'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkelement'})-[:HoortBij]->(l:Asset) 
WHERE pk.typeURI IN ['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkpoort', 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkkaart'] AND pk.isActief AND e.isActief AND l.isActief 
WITH collect(pk) as poortofkaart  
MATCH (a:Asset) 
WHERE a.typeURI CONTAINS 'onderdeel' AND NOT EXISTS((a)-[:HoortBij]->(:Asset {isActief:TRUE})) AND NOT a IN poortofkaart AND a.isActief
RETURN a.uuid, a.naam, a.typeURI"""

r.result_query = result_query
r.run_report()

    

