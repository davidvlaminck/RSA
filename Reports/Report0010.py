from DQReport import DQReport


r = DQReport(name='report0010',
             title='Camera\'s zijn het doel van een Voedt relatie met een Stroomkring of PoEInjector',
             spreadsheet_id='1MzUeaGLeqV78IMBuTTFoM47y4nXja993AZnZF21Zu2U',
             datasource='Neo4J',
             persistent_column='F')

# query that fetches uuids of results
result_query = """OPTIONAL MATCH (c:onderdeel :Camera {isActief:TRUE})<-[r:Voedt]-(o:onderdeel {isActief:TRUE})
WHERE r IS NULL or NOT (o:Stroomkring OR o:PoEInjector)
RETURN c.uuid AS uuid_camera, c.naam AS camera_naam, o.uuid AS voedingsbron_uuid, o.naam AS voedingsbron_naam, o.typeURI"""

r.result_query = result_query
r.run_report()


