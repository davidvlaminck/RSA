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
        , '27db1214-a622-45f8-b124-384598b210f4'  -- ASTRID installatie
        , '9baa5c87-a56e-4ece-9fd0-a0d82a3dc7ec'  -- Radioheruitzend installatie
        , '97b7c30a-f5e9-4008-a3e8-19064146c0c3'  -- Datakabel
        , '3ff63fb2-0234-4e94-a807-5db4dd05a92e'  -- ITSapp
        , 'ae45eec9-b992-4704-a3df-11e8d65d2ad1'  -- Meteostation
        , '4749ba74-ed5a-4811-9428-bcf0e227093a'  -- Elektromotor
        , 'a88493ab-3748-4636-96ed-9c8e8460260d'  -- Toegangscontroller
        , '4e12c432-1546-4bbd-95d9-8fc9bc1e0e02'  -- MIV Meetpunt
        , '7f59b64e-9d6c-4ac9-8de7-a279973c9210'  -- MIV-module
        , 'b6f86b8d-543d-4525-8458-36b498333416'  -- Netwerkelement
        , '50f7400a-2e67-4550-b135-08cde6f6d64f'  -- DynBordVMS
        , '0515e9bc-1778-43ae-81a9-44df3e2b7c21'  -- DynBordRVMS
        , '4aabd323-5480-4771-b33f-28d5c6d46cee'  -- DynBordPK
        , 'fcc947c6-5923-4d56-96fc-73ce4b0bae7f'  -- DynBordGroep
        , '87ef5c66-1f50-4010-a47c-90027ad72421'  -- Hoogtedetectie
        , '9826b683-02fa-4d97-8680-fbabc91a417f'  -- DynBordRSS
        , 'fcc947c6-5923-4d56-96fc-73ce4b0bae7f'  -- DynBordGroep
        , '40b2e487-f4b8-48a2-be9d-e68263bab75a'  -- Seinbrug
        , '615356ae-64eb-4a7d-8f40-6e496ec5b8d7'  -- Galgpaal
        , '6d7544da-2688-4e87-b9e1-305a9009ba18'  -- Z30Groep
        , '4afb0d67-bf8f-4e0e-8544-6af1f296f6bf'  -- DynBordZ30
        , '8d9f83fa-0e19-47ec-902f-ac2c538dd6d9'  -- Lichtmast
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
order by at.uri, a.naampad
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
