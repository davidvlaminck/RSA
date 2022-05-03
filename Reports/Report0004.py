from DQReport import DQReport

if __name__ == '__main__':
    r = DQReport(name='report0004',
                 title='Verkeersregelaars hebben een unieke naam',
                 spreadsheet_id='1aGZFPAeFgkQgU2XcrKhVKK1NPu-OEPuskPvWsnAyEYU',
                 datasource='Neo4J',
                 persistent_column='C')

    # query that fetches uuids of results
    result_query = """MATCH (a:Asset :Verkeersregelaar {isActief:TRUE}) 
WITH a.naam AS naam, COUNT(a.naam) AS aantal
WHERE aantal > 1
WITH collect(naam) AS namen
MATCH (b:Asset :Verkeersregelaar {isActief:TRUE})
WHERE b.naam IN namen
RETURN b.uuid, b.naam"""
    
    r.result_query = result_query
    r.run_report()
    

