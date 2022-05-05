from DQReport import DQReport


r = DQReport(name='report0011',
             title='Omvormers en PoEInjectors hebben een HoortBij relatie naar OmvormerLegacy of Encoder objecten',
             spreadsheet_id='1MQ4Xw31rYzjTzbfIc3a4VFsNq8a1M3lu6_Ly2OE3Opk',
             datasource='Neo4J',
             persistent_column='C')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (o {isActief:TRUE})-[r:HoortBij]->(i {isActief:TRUE})
WHERE (o:Omvormer OR o:PoEInjector) AND (r IS NULL OR NOT(i:OmvormerLegacy OR i:Encoder))
RETURN o.uuid AS onderdeel_uuid, o.naam AS onderdeel_naam, i.uuid AS installatie_uuid, i.naam AS installatie_naam, i.typeURI"""

r.result_query = result_query
r.run_report()


