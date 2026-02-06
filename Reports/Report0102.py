from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0102(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0102', title='IMKLActivityComplex afgeleiden zonder toezichtgroep',
                               spreadsheet_id='1fbnP-heDtQnG9Q5kF1DA_cn3cY7egNFRgXMB4QaZKZk', datasource='PostGIS',
                               persistent_column='C')

        self.report.result_query = """
SELECT otl.uuid, otl_type.uri
FROM assets imkl
	INNER JOIN assetrelaties dv ON dv.doeluuid = imkl.uuid AND dv.relatietype = 'afbe8124-a9e2-41b9-a944-c14a41a9f4d5' -- DeelVan
	INNER JOIN assets otl ON dv.bronuuid = otl.uuid AND otl.actief = TRUE
	INNER JOIN assettypes otl_type ON otl.assettype = otl_type.uuid
	LEFT JOIN assetrelaties hb ON hb.bronuuid = otl.uuid AND hb.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
	LEFT JOIN assets legacy ON hb.doeluuid = legacy.uuid AND legacy.actief = TRUE
	LEFT JOIN betrokkenerelaties b ON otl.uuid = b.bronassetuuid AND rol = 'toezichtsgroep' 
WHERE imkl.assettype = 'b62ac453-ae96-4630-833a-895c57dbb666' -- IMKL activitycomplex  
	AND (legacy.uuid IS NULL OR legacy.assettype <> '37b4af66-a06f-43fe-a80f-8b4bac9907a9') -- lgc RIOOL
	AND imkl.actief = TRUE AND b.doeluuid IS NULL
"""

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
