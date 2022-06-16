from DQReport import DQReport


r = DQReport(name='report0011',
             title='Omvormers en PoEInjectors hebben een HoortBij relatie naar OmvormerLegacy of Encoder objecten',
             spreadsheet_id='1MQ4Xw31rYzjTzbfIc3a4VFsNq8a1M3lu6_Ly2OE3Opk',
             datasource='Neo4J',
             persistent_column='D')

# query that fetches uuids of results
result_query = """MATCH (o {isActief:TRUE})
WHERE (o:Omvormer OR o:PoEInjector) AND NOT EXISTS ((o)-[:HoortBij]->(:Encoder {isActief:TRUE})) AND NOT EXISTS ((o)-[:HoortBij]->(:OmvormerLegacy {isActief:TRUE}))
WITH o
OPTIONAL MATCH (o)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
RETURN o.uuid, o.naam, a.naam as toezichter"""

r.result_query = result_query
r.run_report()


