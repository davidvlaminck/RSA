from DQReport import DQReport


class Report0107:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0107', title='Geometrie is geldig: in Vlaanderen gelegen',
                               spreadsheet_id='1aUVoYhqKe1k4KwuAyNcfWXkH9uwj1Cls_ufH2j37gNg', datasource='PostGIS',
                               persistent_column='D')

        self.report.result_query = """
WITH cte_bbox (geom) AS (
	values(
		ST_SetSRID(ST_GeomFromText('POLYGON((14697 20939, 14697 246456, 261780 246456, 261780 20939, 14697 20939))'), 31370)
	)
), cte_asset_withGeom as (
	select a.uuid, g.wkt_string, st_setsrid(st_geomfromtext(g.wkt_string), 31370) as geom 
	from assets a
	left join geometrie g on a.uuid = g.assetuuid
	where
		a.actief = true
		and
		g.wkt_string is not null
)
select a.*
FROM cte_asset_withGeom a
left join cte_bbox bbox on st_within(a.geom, bbox.geom) where bbox.geom is null;
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
