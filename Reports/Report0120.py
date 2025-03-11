from DQReport import DQReport


class Report0120:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0120',
                               title='OTL installaties en onderdelen types mogen niet voorkomen in "legacy" boomstructuren',
                               spreadsheet_id='1sBJEGOpcGfrjvBWGAkBU_vnWirsGwq2cL8faX3vdapI',
                               datasource='PostGIS',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
-- whitelist van verweven assettypes
with cte_assets_verweven1 as (
	select
		a.uuid
	from assets a
	where
		a.actief = true
		and
	    a.assettype in (
        'efb995df-057b-4ab8-baa8-4f9918f8ec5e'  -- fietstelinstallatie
        , '8d42ee56-17d3-455e-bd9c-1eb1aad3c1ec'  -- fietsteldisplay
        , 'c0def180-e2a5-40eb-abdd-c752cbab48af'  -- fietstelsysteem
        , '7a175f2f-d195-4fb6-bdb3-84f398629e39'  -- zoutbijlaadplaats
        , 'c575f03c-83c1-41c0-9dc6-3d1232bebe99'  -- silo
        , 'cdcd6d8b-0e73-4f87-a62d-be8744e075db'  -- tank
    )
)
-- whitelist van assets: niet-selectieve detectielus met een 'Sturing'-relatie naar een fietstelsysteem 
, cte_assets_verweven2 as (
	select
		a1.uuid
	from assets a1
	left join assetrelaties rel on a1."uuid" = rel.bronuuid
	left join assets a2 on rel.doeluuid = a2.uuid
	where
		a1.assettype = 'f8da675c-eadc-412e-99bc-de25912c6d07'  -- nietselectievedetectielus
		and a1.actief is true
		and	a2.assettype = 'c0def180-e2a5-40eb-abdd-c752cbab48af'  -- fietstelsysteem
		and a2.actief is true
		and rel.relatietype = '93c88f93-6e8c-4af3-a723-7e7a6d6956ac'  -- sturing
		and rel.actief is true
)
-- main query
select
    a.uuid
    , at.uri
    , a.naampad
    , a.naam
    , a.commentaar 
FROM assets a
left join assettypes at on a.assettype = at.uuid
left join cte_assets_verweven1 whitelist1 on a."uuid" = whitelist1.uuid
left join cte_assets_verweven2 whitelist2 on a."uuid" = whitelist2.uuid
where
    (
    (at.uri like '%installatie%' or at.uri like '%onderdeel%')
    and 
    at.uri not like '%lgc%'
    )
    and
    a.actief = true
    and
    (
    a.naampad != ''
    and
    a.naampad is not null
    and
    a.naampad NOT LIKE 'DA-%'  -- Davie
    and
    a.naampad NOT LIKE 'OTN.%' -- Optisch Transport Netwerk
    and
    a.naampad NOT LIKE 'Netwerkgroepen%'
    )
    and whitelist1.uuid is null
    and whitelist2.uuid is null
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
