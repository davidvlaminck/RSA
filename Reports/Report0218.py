from DQReport import DQReport


class Report0218:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
 LET at_80fdf1b4 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#LS\" LIMIT 1 RETURN at._key)
 LET at_b4361a72 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#HS\" LIMIT 1 RETURN at._key)
 LET at_46dcd9b1 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#HSDeel\" LIMIT 1 RETURN at._key)
 LET at_a9655f50 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#LSDeel\" LIMIT 1 RETURN at._key)
 LET at_1cf24e76 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#HSCabineLegacy\" LIMIT 1 RETURN at._key)
 LET at_f625b904 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#SegC\" LIMIT 1 RETURN at._key)
 LET at_8eda4230 = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#AB\" LIMIT 1 RETURN at._key)

FOR a IN assets
FILTER
  a.AIMDBStatus_isActief == true AND a.assettype_key IN [ at_80fdf1b4, at_b4361a72, at_46dcd9b1, at_a9655f50, at_1cf24e76, at_f625b904, at_8eda4230 ] AND a.geometry == null

LET assettype = FIRST(FOR at IN assettypes FILTER at._key == a.assettype_key LIMIT 1 RETURN at)
LET toezichter = FIRST(FOR t IN identiteiten FILTER t._key == a.toezichter_key LIMIT 1 RETURN t)
LET toezichtgroep = FIRST(FOR tg IN identiteiten FILTER tg._key == a.toezichtgroep_key LIMIT 1 RETURN tg)

SORT a.NaampadObject_naampad ASC

RETURN 
  {
    uuid: a._key, 
    assettype: assettype ? assettype.label : null,
    toestand: a.toestand, 
    naampad: a.NaampadObject_naampad, 
    naam: a.AIMNaamObject_naam,
    toezichter: toezichter.voornaam && toezichter.naam ? concat(toezichter.voornaam, " ", toezichter.naam) : null,
    toezichtgroep: toezichtgroep.naam
  } 
"""
        self.report = DQReport(name='report0218',
                               title='Locatie ontbreekt voor voeding-assets (LS, LSDeel, HS, HSDeel, HSCabine, SegmentController, Afstandsbewaking)',
                               spreadsheet_id='1wxPYC35mwexrhWDEX6FQ_xcr_ZdLX6D4PY0g11nwl1U',
                               datasource='ArangoDB',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = aql_query
        self.report.cypher_query = """
with cte_assets_voeding as (
	select
		a.*
	from assets a
	where
		a.actief is true
		and
		a.assettype in (
			'80fdf1b4-e311-4270-92ba-6367d2a42d47', -- Laagspanningsaansluiting (Legacy)
			'b4361a72-e1d5-41c5-bfcc-d48f459f4048', -- Laagspanningsgedeelte (Legacy)
			'46dcd9b1-f660-4c8c-8e3e-9cf794b4de75', -- Hoogspanning (Legacy)
			'a9655f50-3de7-4c18-aa25-181c372486b1', -- Hoogspanningsgedeelte (Legacy)
			'1cf24e76-5bf3-44b0-8332-a47ab126b87e', -- Hoogspanningscabine (Legacy)
			'f625b904-befc-4685-9dd8-15a20b23a58b', -- Segment controller (Legacy)
			'8eda4230-e7dc-4b72-b02b-26d81aa1f45e' -- Afstandsbewaking (Legacy)
		)
)
-- main query
select
	a."uuid",
	at."label" as assettype,
	a.toestand,
	a.naampad, 
	a.naam
from cte_assets_voeding a
left join assettypes at on a.assettype = at."uuid"
left join locatie l on a.uuid = l.assetuuid
where l.geometry is null
order by a.naampad
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
