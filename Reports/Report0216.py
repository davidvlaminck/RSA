from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0216(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0216',
                               title='Verweven assets hebben geen naampad (zijn niet in een boomstructuur op EM-infra gesitueerd)',
                               spreadsheet_id='17MTZ2N_jVsUyc53zbzPwFGhDS8u1X6xrrexU-Li-OkU',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
select
    a."uuid", 
    a.actief as "asset_status", 
    a.naam, 
    a.naampad, 
    at.uri,
    at."label", 
    at.actief as "assettype_status"
from assets a
left join assettypes at on a.assettype = at."uuid"
where a.actief = true
	and at.actief = true
	and a.naampad is null
	and a.assettype in (
-- 18/02/2025
'efb995df-057b-4ab8-baa8-4f9918f8ec5e'  -- fietstelinstallatie
, '8d42ee56-17d3-455e-bd9c-1eb1aad3c1ec'  -- fietsteldisplay
, 'c0def180-e2a5-40eb-abdd-c752cbab48af'  -- fietstelsysteem
, '7a175f2f-d195-4fb6-bdb3-84f398629e39'  -- zoutbijlaadplaats
, 'cdcd6d8b-0e73-4f87-a62d-be8744e075db'  -- tank
, 'c575f03c-83c1-41c0-9dc6-3d1232bebe99'  -- silo
-- 29/04/2025
, '27db1214-a622-45f8-b124-384598b210f4'  -- ASTRID installatie
, '9baa5c87-a56e-4ece-9fd0-a0d82a3dc7ec'  -- Radioheruitzend installatie
-- temp disabled
--, '97b7c30a-f5e9-4008-a3e8-19064146c0c3'  -- Datakabel
, '3ff63fb2-0234-4e94-a807-5db4dd05a92e'  -- ITSapp
, 'ae45eec9-b992-4704-a3df-11e8d65d2ad1'  -- Meteostation
, '4749ba74-ed5a-4811-9428-bcf0e227093a'  -- Elektromotor
, 'a88493ab-3748-4636-96ed-9c8e8460260d'  -- Toegangscontroller
, '4e12c432-1546-4bbd-95d9-8fc9bc1e0e02'  -- MIV Meetpunt
, '7f59b64e-9d6c-4ac9-8de7-a279973c9210'  -- MIV-module
-- 02/06/2025
, 'b6f86b8d-543d-4525-8458-36b498333416'  -- Netwerkelement
-- 13/06/2025
, '50f7400a-2e67-4550-b135-08cde6f6d64f'  -- DynBordVMS
, '0515e9bc-1778-43ae-81a9-44df3e2b7c21'  -- DynBordRVMS
, '4aabd323-5480-4771-b33f-28d5c6d46cee'  -- DynBordPK
, 'fcc947c6-5923-4d56-96fc-73ce4b0bae7f'  -- DynBordGroep
, '87ef5c66-1f50-4010-a47c-90027ad72421'  -- Hoogtedetectie
-- 17/06/2025
, '9826b683-02fa-4d97-8680-fbabc91a417f'  -- DynBordRSS
, 'fcc947c6-5923-4d56-96fc-73ce4b0bae7f'  -- DynBordGroep
-- 20/06/2025
, '40b2e487-f4b8-48a2-be9d-e68263bab75a'  -- Seinbrug
, '615356ae-64eb-4a7d-8f40-6e496ec5b8d7'  -- Galgpaal
-- 24/06/2025
, '6d7544da-2688-4e87-b9e1-305a9009ba18'  -- Z30Groep
, '4afb0d67-bf8f-4e0e-8544-6af1f296f6bf'  -- DynBordZ30
-- 27/06/2025
, '8d9f83fa-0e19-47ec-902f-ac2c538dd6d9'  -- Lichtmast
-- extra verwerven
, '6d518126-d229-4446-89ee-1ae2a9be4318'  -- Stralende Kabel
, '48afe679-1483-46dd-ac5e-b3f2f97506bf'  -- Zuil toegangscontrole
-- 2/10/2025 en 3/10/2025
, '7044685e-dfdb-421c-9825-2c268b7d2e2f'  -- Dynamisch Bord Externe Processing Unit
, '79ecb22b-e1ff-4032-a95b-a33c69d15135'  -- Cabine
-- 23/10/2025
, '3f98f53a-b435-4a69-af3c-cede1cd373a7'  -- Camera
, '788e72fa-24b8-4f4c-8ed7-d8448c9cd76f'  -- Cameragroep
, '30a173e5-bb95-4391-b533-99adcdba033c'  -- Omvormer
, '6e61fb1c-ebff-49e2-8fe0-45fc24626991'  -- Power over Ethernet (PoE) Injector
-- 20/11/2025
, '052aa583-f54c-4f03-9c17-09995bb28a5d'  -- Illuminator
-- verweving eind november
, 'df9f19eb-5eb3-49d9-b782-6b22cfb8993b'  -- Bel
, 'be55ecdf-aa99-4dac-b00a-6ad4f9f6b615'  -- Calamiteitendoorsteek 
, '99c0e9c3-0aea-4648-86b4-45a16a5a5ee4'  -- Calamiteitendoorsteekgroep
, '0f55b669-2b77-4812-ae6f-867749fc76ac'  -- Slagboom
, 'bf2b7871-47ec-468c-93ba-7a2833389b3e'  -- Slagboomgroep
, '2c73932c-fa50-4677-89fb-778393263488'  -- Kokerafsluiting
, 'd5705624-233f-4e05-9574-86dd9c98b4e5'  -- Hulppost
, 'c7d996a9-00e2-4ddf-af81-3f7eb76cbc8a'  -- Hulppostgroep
, 'a58ed6fe-e930-41b4-baa4-b7f7950b5b3b'  -- Inwenvig verlicht pictogram
, 'c3106313-4b66-44cb-b885-39ae91fdf00e'  -- Brandblusser
, '86dc2408-ff32-42a7-a393-718a5f9fcf91'  -- Luchtkwaliteit zender ontvanger
, '07f28457-3123-4bd8-baee-8504c027d358'  -- Luchtkwaliteitsensor
, '9cb182d9-d893-43e4-b998-09cd950bccd5'  -- Noodverlichtingstoestel
, '42efc21e-8424-4680-a611-d0f04d2a215c'  -- Intercomtoestel
, '664a09b8-ce64-49a1-9cc4-b575ab072095'  -- Intercomserver
, 'd3e26758-6b3d-4ee9-b04e-238eefe86e43'  -- Deur
, 'cf53f4fd-a8ca-413a-83c4-1c670fab7a5e'  -- Contourverlichting
, '6e9010da-507f-426c-a4c5-f3a49baacb8a'  -- Kokerventilatie
, 'f815c084-ac38-4f9b-8bc3-a501ef6c227f'  -- Ventilatiecluster
, '69462525-65de-4951-8442-57cbc24fe598'  -- Ventilator
, 'f11afc31-c780-4630-a5e4-7147abb4987a'  -- Ventilatie afsluitklep
, '015f6cc2-7daa-4578-a360-01c810feaff6'  -- Tunneluitrusting
, '10088403-228d-43f7-9aa6-66469d2e7760'  -- Pomp
, '3d6b7eca-e4d6-40bd-ba98-1059efcba670'  -- Drukverhogingsgroep
, 'e889caba-ad57-43e1-8b1a-7ad3b11dd57a'  -- Gassensor
, 'fe26c074-edf3-4307-a4dc-1a9c18001325'  -- Lichtsensor
, 'd9904200-b625-433f-8f3e-2eb8d5db091c'  -- Luchtkwaliteitssensor
, 'fbf9755a-5f67-4dc9-9637-03331aa0780b'  -- Tunnelverlichting
-- verweving 4/12/2025
, '217ba1cb-43a7-464c-a968-ac2582e45207' -- Flitsgroep
, '4cd16712-1ee7-460f-9729-08da0c87e947' -- Flitspaal
, '3e8bd99a-8e6f-4653-aab4-b5be694ccb10' -- Flitscamera
, '47777ce0-09c3-42ca-a9bb-a685717ace57' -- UitleesapparatuurFlitscamera        
-- verweving 9/12/2025
, 'd93fb220-f0e5-40cd-9f5d-2416140cb19e'  -- DynBordOpMaat
, '40b2e487-f4b8-48a2-be9d-e68263bab75a'  -- Seinbrug
-- verweving 12/12/2025
, 'ba0e8976-aff6-43d6-8c3e-db65f096f251'  -- BiFlash
, '800f0a16-773c-473e-82a3-e471a3c7246f'  -- BiFlashInstallatie
-- verweving Q1 2026
--, '83552f3c-4944-40d8-8e63-33e48533210b'  -- Laagspanningsbord
--, 'b4ee4ea9-edd1-4093-bce1-d58918aee281'  -- DNBLaagspanning
--, 'ffb9a236-fb9e-406f-a602-271b68e62afc'  -- Forfaitaire aansluiting
--, 'ca3ae27f-c611-4761-97d1-d9766dd30e0a'  -- Energiemeter DNB
--, 'c3601915-3b66-4bde-9728-25c1bbf2f374' -- Wegkantkast
--, '6ea11739-4bba-4a7c-8cac-a2c135d91d9c' -- Wegverlichtingroep
--, '9e557bed-608b-4704-b1dd-54ad0bb64d7a' -- VerlichteOversteekplaatsGroep
--, '6c1883d1-7e50-441a-854c-b53552001e5f' -- Segmentcontroller
--, 'a8623da1-6d99-4528-a947-3782984a0294'  -- CabineController
--, '855812a3-a32f-4968-9238-46dbe29e4289'  -- Pompstation
--, 'abb7572e-fa82-4d45-b3ca-b06abdd7cfa4'  -- Geleidingsverlichting
-- verweving Q2 2026 (in overleg met Edison)
--, '478add39-e6fb-4b0b-b090-9c65e836f3a0' -- WVLichtmast
--, 'e78ce094-565b-4e8c-a956-88c105367a4f' -- WVConsole
--, '12b2af6b-72e1-4028-b6ed-3d3b654735d4' -- WVBevestigd
--, '622ac17d-2ea7-46bb-9c36-c47794404ef2' -- Punctuele verlichtingsmast
-- overige        
--, 'e67900b1-88fb-44da-9285-409f7f67147f'  -- BinnenverlichtingGroep
)
order by at.uri asc, a.naam asc
            """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
