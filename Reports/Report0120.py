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
        , '6d518126-d229-4446-89ee-1ae2a9be4318'  -- Stralende Kabel
        , '48afe679-1483-46dd-ac5e-b3f2f97506bf'  -- Zuil toegangscontrole
        -- verweving september
        --, 'df9f19eb-5eb3-49d9-b782-6b22cfb8993b'  -- Bel
        --, 'be55ecdf-aa99-4dac-b00a-6ad4f9f6b615'  -- Calamiteitendoorsteek
        --, '0f55b669-2b77-4812-ae6f-867749fc76ac'  -- Slagboom
        --, 'd5705624-233f-4e05-9574-86dd9c98b4e5'  -- Hulppost
        --, 'a58ed6fe-e930-41b4-baa4-b7f7950b5b3b'  -- Inwenvig verlicht pictogram
        --, 'c3106313-4b66-44cb-b885-39ae91fdf00e'  -- Brandblusser
        --, '86dc2408-ff32-42a7-a393-718a5f9fcf91'  -- Luchtkwaliteit zender ontvanger
        --, '07f28457-3123-4bd8-baee-8504c027d358'  -- Luchtkwaliteitsensor
        --, '9cb182d9-d893-43e4-b998-09cd950bccd5'  -- Noodverlichtingstoestel
        --, '42efc21e-8424-4680-a611-d0f04d2a215c'  -- Intercomtoestel
        --, '664a09b8-ce64-49a1-9cc4-b575ab072095'  -- Intercomserver
        --, 'd3e26758-6b3d-4ee9-b04e-238eefe86e43'  -- Deur
        --, 'cf53f4fd-a8ca-413a-83c4-1c670fab7a5e'  -- Contourverlichting
        --, 'abb7572e-fa82-4d45-b3ca-b06abdd7cfa4'  -- Geleidingsverlichting
        --, '6e9010da-507f-426c-a4c5-f3a49baacb8a'  -- Kokerventilatie
        --, 'f815c084-ac38-4f9b-8bc3-a501ef6c227f'  -- Ventilatiecluster
        --, '69462525-65de-4951-8442-57cbc24fe598'  -- Ventilator
        --, '015f6cc2-7daa-4578-a360-01c810feaff6'  --  Tunneluitrusting
        --, '10088403-228d-43f7-9aa6-66469d2e7760'  -- Pomp
        --, '855812a3-a32f-4968-9238-46dbe29e4289'  -- Pompstation
        --, 'e889caba-ad57-43e1-8b1a-7ad3b11dd57a'  -- Gassensor
        --, 'fe26c074-edf3-4307-a4dc-1a9c18001325'  -- Lichtsensor
        --, 'fbf9755a-5f67-4dc9-9637-03331aa0780b'  -- Tunnelverlichting
        --, 'e67900b1-88fb-44da-9285-409f7f67147f'  -- BinnenverlichtingGroep
        , '7044685e-dfdb-421c-9825-2c268b7d2e2f'  -- Dynamisch Bord Externe Processing Unit
        , '79ecb22b-e1ff-4032-a95b-a33c69d15135'  -- Cabine
        -- verweving oktober
        --, '3f98f53a-b435-4a69-af3c-cede1cd373a7'  -- Camera
        --, '788e72fa-24b8-4f4c-8ed7-d8448c9cd76f'  -- Cameragroep
        --, '30a173e5-bb95-4391-b533-99adcdba033c'  -- Omvormer
        --, '6e61fb1c-ebff-49e2-8fe0-45fc24626991'  -- Power over Ethernet (PoE) Injector
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
