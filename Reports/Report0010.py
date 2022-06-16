from DQReport import DQReport


r = DQReport(name='report0010',
             title='Camera\'s zijn het doel van een Voedt relatie met een Stroomkring of PoEInjector',
             spreadsheet_id='1MzUeaGLeqV78IMBuTTFoM47y4nXja993AZnZF21Zu2U',
             datasource='Neo4J',
             persistent_column='D')

# query that fetches uuids of results
result_query = """MATCH (c:Camera {isActief:TRUE})
WHERE NOT EXISTS ((c)<-[:Voedt]-(:Stroomkring {isActief:TRUE})) AND NOT EXISTS ((c)<-[:Voedt]-(:PoEInjector {isActief:TRUE}))
WITH c
OPTIONAL MATCH (c)-[:HeeftBetrokkene {rol:'toezichter'}]->(a:Agent)
RETURN c.uuid, c.naam, a.naam as toezichter"""

r.result_query = result_query
r.run_report()


