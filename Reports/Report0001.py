class Report:
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = ''):
        self.summary_sheet_id = '1s_oro-4tJy_1R1G99TTPnL4-5ACR4BD-R1XWFvFuviQ'
        self.name = name
        self.title = title
        self.spreadsheet_id = spreadsheet_id
        self.datasource = datasource


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource)


if __name__ == '__main__':
    r = DQReport(name='report0001',
                 title='Onderdelen hebben een HoortBij relatie',
                 spreadsheet_id='16iUSRuS9M85P4E7Mi5-1J8pWgPr6Ehp1liEmRaZFNi4',
                 datasource='Neo4J')

    # query that fetches uuids of results
    result_query = """MATCH (pk:Asset)-[:Bevestiging]-(e:Asset {typeURI:'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkelement'})-[:HoortBij]->(l:Asset) 
WHERE pk.typeURI IN ['https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkpoort', 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Netwerkkaart'] AND pk.isActief AND e.isActief AND l.isActief 
WITH collect(pk) as poortofkaart  
MATCH (a:Asset) 
WHERE a.typeURI CONTAINS 'onderdeel' AND NOT EXISTS((a)-[:HoortBij]->(:Asset {isActief:TRUE})) AND NOT a IN poortofkaart AND a.isActief
RETURN a.uuid, a.typeURI"""

