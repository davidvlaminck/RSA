from DQReport import DQReport


class Report0184:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0184', title='Laagspanningsaansluiting (Legacy) keuringsinfo',
                               spreadsheet_id='1tFLD_Ah9V3S6V3RcFsToEs7OWW5U26q6TIuOW5jLHrI', datasource='PostGIS',
                               persistent_column='N', link_type='eminfra')

        self.report.result_query = """
with
cte_laagspanningsaansluiting as (
	select
		a.uuid
		, a.naampad
		, at.uri
		, a.actief
		, a.toestand
		, a.commentaar
		, gem.gemeente
		, gem.provincie
	from assets a
	left join assettypes at on a.assettype = at.uuid
	left join locatie l on a.uuid = l.assetuuid
	left join gemeente gem on st_dwithin(l.geometry, gem.geom, 0)
	where
		a.actief is true
		and
		a.assettype = '80fdf1b4-e311-4270-92ba-6367d2a42d47'  -- Laagspanningsaansluiting (Legacy)
)
, cte_attribuutwaarden_grouped as (
	SELECT 
	    assetuuid,
	    MAX(waarde) FILTER (WHERE attribuutuuid = 'ffad4ca4-a393-40fc-a6bd-ffb1ed2b718b') AS datum_eerste_controle,
	    MAX(waarde) FILTER (WHERE attribuutuuid = '7c34fa88-4740-409a-8316-88e250f49548') AS datum_laatste_controle,
	    MAX(waarde) FILTER (WHERE attribuutuuid = 'fef12239-764e-4068-9f76-73f0d6bb6446') AS resultaat_keuring
	FROM attribuutwaarden
	WHERE attribuutuuid IN (
	    'ffad4ca4-a393-40fc-a6bd-ffb1ed2b718b', -- datum eerste controle
	    '7c34fa88-4740-409a-8316-88e250f49548', -- datum laatste controle
	    'fef12239-764e-4068-9f76-73f0d6bb6446'  -- resultaat keuring
	)
	GROUP BY assetuuid
)
select
	ls.*
	, aw.datum_eerste_controle
	, aw.datum_laatste_controle
	, aw.resultaat_keuring
	, (coalesce(aw.datum_laatste_controle, aw.datum_eerste_controle)::date + interval '5 year')::date as vervaldag_keuring
	, EXTRACT(DAY FROM (coalesce(aw.datum_laatste_controle, aw.datum_eerste_controle)::date + interval '5 year' - CURRENT_DATE)) as aantal_resterende_dagen_tot_vervaldag_keuring
from cte_laagspanningsaansluiting ls
left join cte_attribuutwaarden_grouped aw on ls.uuid = aw.assetuuid
order by aantal_resterende_dagen_tot_vervaldag_keuring
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
