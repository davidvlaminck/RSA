from DQReport import DQReport

if __name__ == '__main__':
    r = DQReport(name='report0005',
                 title='Verkeersregelaars en TLCfiPoorten hebben een HoortBij relatie naar VRLegacy objecten',
                 spreadsheet_id='1daDivHkKfMRamwgpty9swGF4Kz68MBjJlSE5SR2GqFQ',
                 datasource='Neo4J',
                 persistent_column='D')

    # query that fetches uuids of results
    result_query = """MATCH (a:Asset {isActief:TRUE}) 
WHERE (a:Verkeersregelaar OR a:TLCfiPoort) AND NOT EXISTS ((a)-[:HoortBij]->(:VRLegacy {isActief:TRUE}))
RETURN a.uuid, a.naam, a.typeURI"""
    
    r.result_query = result_query
    r.run_report()
    

