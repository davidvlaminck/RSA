from DQReport import DQReport


class Report0102:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0102', title='IMKLActivityComplex afgeleiden zonder toezichtgroep',
                               spreadsheet_id='1fbnP-heDtQnG9Q5kF1DA_cn3cY7egNFRgXMB4QaZKZk', datasource='PostGIS',
                               persistent_column='C')

        self.report.result_query = """
SELECT otl.uuid, a2.uri 
FROM assets 
    LEFT JOIN assetrelaties a ON a.doeluuid = assets.uuid AND a.relatietype = 'afbe8124-a9e2-41b9-a944-c14a41a9f4d5'
    LEFT JOIN assets otl ON a.bronuuid = otl.uuid 
    LEFT JOIN assettypes a2 ON otl.assettype = a2.uuid
    LEFT JOIN betrokkenerelaties b ON otl.uuid = b.bronuuid AND rol = 'toezichtgroep'
WHERE assets.assettype = 'b62ac453-ae96-4630-833a-895c57dbb666' AND assets.actief = TRUE AND 
    assets.assettype <> '37b4af66-a06f-43fe-a80f-8b4bac9907a9' AND otl.uuid IS NOT NULL AND b.doeluuid IS NULL;
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
