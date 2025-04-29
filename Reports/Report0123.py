from DQReport import DQReport


class Report0123:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0123',
                               title='Geometrie is geldig: realistische grootte',
                               spreadsheet_id='1gbwsmeKicH0_IJVfK05JD4RC93RkWa9zVUO1TEpLqxA',
                               datasource='PostGIS',
                               persistent_column='E'
                               )

        self.report.result_query = """
        with cte_assettypes_whitelist (uuid) as (
            select uuid
            from assettypes
            where uri in (
                'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AanvullendeGeometrie'
                , 'https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#ActivityComplex'
                , 'https://grp.data.wegenenverkeer.be/ns/installatie#IMKLActivityComplex'
                , 'https://grp.data.wegenenverkeer.be/ns/installatie#IMKLExtraPlan'
                , 'https://grp.data.wegenenverkeer.be/ns/installatie#IMKLPipe'
                , 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geleideconstructie'
            )
        )
        , cte_assets_whitelist (uuid) as (
            values
                ('e5bfa05c-cf08-431a-aa8c-13968d6c0ac4'::uuid)
                , ('6797d3d0-8470-4814-9278-f7095a166719'::uuid)
                , ('a59989c2-474e-4fb8-b085-e3ac2777a391'::uuid)
                , ('be90f958-86e7-432c-841a-b50ab51bc552'::uuid)
                , ('74101609-6b80-4450-ac32-2c10aa0ad62d'::uuid)
                , ('81acc56b-a034-4028-9cbc-6923b5a29f47'::uuid)
                , ('a82e832a-73df-4cbb-9d6c-c801ae7777d6'::uuid)
                , ('53800268-161b-4200-9d95-99f1d4335e6f'::uuid)
                , ('45dfb7e3-2bdc-4683-a894-2d74502f77d3'::uuid)
                , ('f527bfbe-fac6-4140-8d29-e3cd33365068'::uuid)
                , ('ecafa92f-b9ab-41d8-a9ec-59f40ccbbda4'::uuid)
                , ('72cc0b0d-59fe-4142-a083-ba4ad5100265'::uuid)
                , ('b09b6522-4c48-4b3f-ae50-ece929ac9337'::uuid)
                , ('d4164a12-acdd-4c67-9685-deb933fbc6e1'::uuid)
                , ('3a03eb0c-d6d5-4154-8f67-b6fdee9385fd'::uuid)
                , ('ee543f31-5602-4bb3-8a8f-53f03e040695'::uuid)
                , ('dfcbe804-4e06-44f8-b89d-4e647638a8c4'::uuid)
                , ('20c1f4eb-69f9-4d26-9248-c650d5e39d09'::uuid)
                , ('0e90552c-b536-46b3-bea3-1d78e8da5721'::uuid)
                , ('28143705-b7c9-4ab6-887d-af4c82561720'::uuid)
                , ('9ff5debe-0771-45f8-bb21-fc0ae5a0ff83'::uuid)
                , ('8238cc00-1abc-4a8b-8a37-be34ee230d22'::uuid)
                , ('74a6724d-7d8d-42f1-8333-3f97b89a4b96'::uuid)
                , ('bae492f8-538c-471b-aeb6-7383ad45a1d8'::uuid)
                , ('c85ef953-2e2b-4345-8ace-332af31f89c2'::uuid)
                , ('ea02042e-5356-424a-9c2a-8e5b7eda9ff6'::uuid)
                , ('208c9045-b0cb-469d-88bc-a22b6ac42015'::uuid)
                , ('46f0070a-5b0b-421c-bcb6-49ed137257f4'::uuid)
                , ('11d66480-783d-437f-86ea-8a71fcaeb14d'::uuid)
                , ('cb8d1939-9d71-49ab-a96d-9189219614e2'::uuid)
                , ('f5d15aae-b221-4a71-9c92-d0031274b13f'::uuid)
                , ('2a2a9963-a89c-4def-8b1f-c7fea8925f9d'::uuid)
                , ('23c39704-71d9-411a-9cab-57496384f063'::uuid)
                , ('866dac85-81de-49e6-aeab-f7ec07ddd92c'::uuid)
                , ('d735d3e2-90d6-4960-b33c-76be076b4f91'::uuid)
                , ('863e40dd-11da-460c-8851-5bf2d01fdd85'::uuid)
                , ('7e2e66a6-8beb-4852-8810-7747cdcbda47'::uuid)
                , ('22ef8e79-9c63-4c33-961a-65775735077c'::uuid)
                , ('779baf5b-e46e-45bd-89fb-8adfe1747028'::uuid)
                , ('2331e2e4-0b38-461d-9f3a-8ae08a9424ab'::uuid)
                , ('a20fd526-0cf1-4d9f-8fc0-f698f9274030'::uuid)
                , ('0eac92d3-6e82-4962-ba18-6a302305e4a2'::uuid)
                , ('2f834ee2-9de3-4b18-8bae-3608c3a1192c'::uuid)
                , ('e84f1cf6-6541-49c8-ba47-94c73ae962da'::uuid)
                , ('527f736d-7625-4e95-a46c-a97d1b1c6f2c'::uuid)
                , ('8c71fa35-88eb-48b4-901e-519b565eec72'::uuid)
                , ('9eb1b523-1a45-48f1-93a8-b2da879889c0'::uuid)
                , ('5ccd406b-c6af-4fd5-b486-b12fced3c5db'::uuid)
                , ('a289de98-799e-47ad-af2f-9c2c0e5d2b79'::uuid)
                , ('31e59cfe-7caf-402e-9177-38764657db09'::uuid)
                , ('d43c9511-33b4-4cb7-a81f-1a74d1feb930'::uuid)
                , ('e078f596-f980-49e7-a269-9f402805aac9'::uuid)
                , ('c6717118-dfd2-4b3a-ba14-9ca905437b30'::uuid)
                , ('13e5848a-939a-4161-898d-b5f74e434fed'::uuid)
                , ('ee54e7e0-3962-40c7-af6f-889798cf6a28'::uuid)
                , ('c12ef4c8-9243-4e1f-9fba-de5175485d9a'::uuid)
                , ('0db07aa4-1fa5-40f9-b2cf-0b5adfe28f61'::uuid)
                , ('0b85028e-82ff-4f7b-9d8d-5517d80b0d58'::uuid)
                , ('be96ef21-79ee-4361-9c83-f325b07caaca'::uuid)
                , ('5b6f1944-eb75-4378-b90f-b9eab75bde80'::uuid)
                , ('7626f4e0-685d-47ac-819d-ce5f4ecf14d3'::uuid)
                , ('39e0391a-1dcc-45b9-8b3e-495fbd55bee7'::uuid)
                , ('e6280cda-5cb1-4424-a102-687e3db695f2'::uuid)
                , ('6b2ec02a-ac0c-445d-be59-633ac2ddd6de'::uuid)
                , ('17c0d1c9-938b-4412-a03e-5cfb4c4958c7'::uuid)
                , ('282fe945-a976-4fd1-b445-68a419686116'::uuid)
                , ('2e78f2e1-4a5c-495b-a8fe-ac3c334870bd'::uuid)
                , ('9a328f1a-8b9c-47c9-9df7-9ab3d00e53e2'::uuid)
        )
        , cte_assets_met_oppervlakte as (
        select
            a.uuid
            , at.naam
            , at.uri
            , left(g.wkt_string, 50000) as wkt_string
            , st_setsrid(st_geomfromtext(g.wkt_string), 31370) as geom
            , st_area(st_orientedenvelope(st_setsrid(st_geomfromtext(g.wkt_string), 31370))) as oppervlakte	
        from assets a
        left join assettypes at on a.assettype = at.uuid
        left join geometrie g on a.uuid = g.assetuuid
        where
            a.actief = true
            and
            at.uuid not in (select * from cte_assettypes_whitelist)
            and
            at.uuid not in (select * from cte_assets_whitelist)
            and
            st_area(st_orientedenvelope(st_setsrid(st_geomfromtext(g.wkt_string), 31370))) > 10000000
        )
        -- main query
        select uuid, naam, uri, oppervlakte
        from cte_assets_met_oppervlakte
        where 
            -- groter dan 10 vierkante kilometer
            -- st_area(st_orientedenvelope(st_setsrid(st_geomfromtext(g.wkt_string), 31370))) > 10000000
            oppervlakte > 10000000
        order by naam asc, oppervlakte desc        
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
