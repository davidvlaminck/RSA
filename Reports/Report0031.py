from DQReport import DQReport


class Report0031:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0031',
                               title="Netwerkelementen met gebruik 'L2-switch' hebben een hoortbij relatie naar installatie L2AccesStructuur",
                               spreadsheet_id='1k5uUwLmf5IFVhftY7klBmylWtuEBwP8URjYPMcAB71w',
                               datasource='PostGIS',
                               persistent_column='C')

        self.report.result_query = """
WITH elementen AS (
	SELECT * 
	FROM assets 
	WHERE assettype = 'b6f86b8d-543d-4525-8458-36b498333416' AND actief = TRUE), -- Netwerkelement
relaties AS (
	SELECT assetrelaties.* 
	FROM assetrelaties
		LEFT JOIN assets ON assets.uuid = doeluuid AND assets.actief = TRUE AND assets.assettype = '30b571a9-77ef-4289-a458-139882a5e97a' -- L2AccessStructuur
	WHERE relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2') -- HoortBij
SELECT elementen.uuid, elementen.naam  
FROM elementen
	LEFT JOIN relaties ON elementen.uuid = relaties.bronuuid
WHERE relaties.uuid IS NULL;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
