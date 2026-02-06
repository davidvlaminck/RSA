from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0171(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0171',
                               title='Assets conform naamconventies OTL EW-Infrastructuur',
                               spreadsheet_id='1t6s3fYOdRybNUOPXlI2O4sHACAb3tYcGlEHnelhogF4',
                               datasource='PostGIS',
                               persistent_column='H'
                               )

        self.report.result_query = """
with cte_lookup_table ("assettype", "assetnaam", "regexp_pattern") as (
    values
        -- HS/LS
          ('d76cbedd-5488-428c-a221-fe0bc8f74fa2'::uuid, 'hscabine', '^(A|C|G|WO|WW)[0-9]{4}\.HS$')
        , ('c3601915-3b66-4bde-9728-25c1bbf2f374'::uuid, 'lskast', '^(A|C|G|WO|WW)[0-9]{4}\.(LS\d*)$')
        , ('83552f3c-4944-40d8-8e63-33e48533210b'::uuid, 'laagspanningsbord', '^(A|C|G|WO|WW)[0-9]{4}\.LSB\d*$')
        , ('4c76f8ae-8ca7-4563-b5a8-01fff2f02883'::uuid, 'hoofdschakelaar', '^(A|C|G|WO|WW)[0-9]{4}\.HS\d*$')
        , ('ca3ae27f-c611-4761-97d1-d9766dd30e0a'::uuid, 'energiemeterdnb', '^(A|C|G|WO|WW)[0-9]{4}\.(EM\d{1})$')
        , ('a8623da1-6d99-4528-a947-3782984a0294'::uuid, 'cabinecontroller', '^(A|C|G|WO|WW)[0-9]{4}\.(CC\d{1})$')
        , ('6c1883d1-7e50-441a-854c-b53552001e5f'::uuid, 'segmentcontroller', '^(A|C|G|WO|WW)[0-9]{4}\.(SC\d{1})$')
        , ('1a0bf7cb-c0e1-4e56-9cd6-79f28f38a1d1'::uuid, 'aftakking', '^(A|C|G|WO|WW)[0-9]{4}\.((MQ|OQ|GQ|PQ)\d{1})$')
        , ('a82d9162-adf2-4b3f-9a7b-cd48f15e71b8'::uuid, 'stroomkring', '^(A|C|G|WO|WW)[0-9]{4}.*\.(SK(A|\d{1}))$')
        , ('01ae437c-02f2-4f9b-85be-09618376346e'::uuid, 'aardingsinstallatie', '^(A|C|G|WO|WW)[0-9]{4}\.AI$')
        , ('bc44935d-b83b-46ce-a158-e0e874f227c6'::uuid, 'aardingskabel', '^(A|C|G|WO|WW)[0-9]{4}\.AK.*$')
        , ('4834b49b-f198-4632-b4dc-6d49d557a42a'::uuid, 'voedingskabel', '^(A|C|G|WO|WW)[0-9]{4}\.VKA.*$')
        , ('a6762420-105d-4623-9a42-12387fafc7ec'::uuid, 'kabelmof', '^(A|C|G|WO|WW)[0-9]{4}\.VKA\.MOF$')
        , ('8e9307e2-4dd6-4a46-a298-dd0bc8b34236'::uuid, 'dnbhoogspanning', '^(A|C|G|WO|WW)[0-9]{4}\.DNB\.HS$')
        , ('b4ee4ea9-edd1-4093-bce1-d58918aee281'::uuid, 'dnblaagspanning', '^(A|C|G|WO|WW)[0-9]{4}\.DNB\.LS$')
        -- IVS Inwendig verlichte signalisatieborden
        , ('fc2f4c46-9f46-48f2-b84c-d23d21131df6'::uuid, 'hefportiek', '^(A|C|G|WO|WW)[0-9]{4}\.S\d*$')
        , ('615356ae-64eb-4a7d-8f40-6e496ec5b8d7'::uuid, 'galgpaal', '^(A|C|G|WO|WW)[0-9]{4}\.(T|G)\d*$')
        , ('556061ca-ecd8-42c7-81fd-9163930f080b'::uuid, 'montagekast', '^(A|C|G|WO|WW)[0-9]{4}\.(T|C)\d*.MK\d*$')
        , ('47a95414-664c-48d2-993f-2406fc106558'::uuid, 'IVSB groep (legacy)', '^(A|C|G|WO|WW)[0-9]{4}\.T\d*.IVSB\d*$')
        , ('06d5c91f-6538-47d6-86c2-8b680f6a2423'::uuid, 'LED-driver', '^(A|C|G|WO|WW)[0-9]{4}\.(T|C)\d*.(IVSB|WV)\d*.LD\d*$')
        , ('17da1bf3-5272-4b35-b722-30dbaa0d901f'::uuid, 'armatuurcontroller', '^(A|C|G|WO|WW)[0-9]{4}\.(T|C)\d*.(IVSB|WV)\d*.AC\d*$')
        , ('fea05a3c-a787-4a7b-9edb-05be3b4174e0'::uuid, 'lichtzuil', '^(A|C|G|WO|WW)[0-9]{4}\.L\d*$')
        , ('1e167364-cdd8-43cd-bebf-e4bbf492ee90'::uuid, 'lichtnagel', '^(A|C|G|WO|WW)[0-9]{4}\.L\d*$')
        , ('ea7eb1e3-a197-4b0d-8bbb-43c32c1efcbb'::uuid, 'bochtafbakening', '^(A|C|G|WO|WW)[0-9]{4}\.BAF\d*$')
        , ('21f6c54e-6a1c-4774-886f-9e0b0cc910ad'::uuid, 'LED wegdekreflector bebakening', '^(A|C|G|WO|WW)[0-9]{4}\.LWR\d*$')
        , ('eee2b6c6-0eb0-496a-805e-4e8777ab5a62'::uuid, 'LED rotondeafbakening', '^(A|C|G|WO|WW)[0-9]{4}\.RAF\d*$')
        -- WV (Wegverlichting)
        , ('622ac17d-2ea7-46bb-9c36-c47794404ef2'::uuid, 'punctuele verlichtingsmast', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*$')
        , ('e78ce094-565b-4e8c-a956-88c105367a4f'::uuid, 'WV concole', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*$')
        , ('4c68c109-85be-4183-af59-104ff6ec1825'::uuid, 'Bevestiging voor verliching (legacy)', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*$')
        , ('9cb182d9-d893-43e4-b998-09cd950bccd5'::uuid, 'Noodverlichtingstoestel', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('1c065bd6-654e-44b9-b6fc-8a3b05578014'::uuid, 'Verlichtingstoestel MH HP', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('32dfcf3d-6e53-43ae-bd51-7204019c910e'::uuid, 'Binnenverlichtingstoestel', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('929c6289-734f-4949-b5ce-30b05836c19c'::uuid, 'Verlichtingstoestel LED', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('91b6342f-cd70-4683-a070-4f2affb786e8'::uuid, 'Verlichtingstoestel Hg LP', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('4a75c2d1-fd98-4a7b-905c-20b287ba35ef'::uuid, 'Verlichtingstoestel TL', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('4fc70727-f4ae-4273-bf3b-4e4cb26bdb33'::uuid, 'Verlichtingstoestel Na LP', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('24111bed-1a67-4620-a97c-a60d218cece8'::uuid, 'Verlichtingstoestel Na HP', '^(A|C|G|WO|WW)[0-9]{4}\.C\d*\.WV\d*$')
        , ('ba0e8976-aff6-43d6-8c3e-db65f096f251'::uuid, 'biflash', '^(A|C|G|WO|WW)[0-9]{4}\.T\d*\.BIF\d*$')
        , ('a5aefdf1-8bd5-4661-a780-0eebd6fad030'::uuid, 'retroreflecterendverkeersbord', '^(A|C|G|WO|WW)[0-9]{4}\.T\d*\.RV\d*$')
        , ('5380695a-bb17-4f2a-91bb-9cb8c159245c'::uuid, 'retroreflecterendefolie', '^(A|C|G|WO|WW)[0-9]{4}\.T\d*\.RV\d*\.RF$')
)
--select * from cte_lookup_table
, cte_assets as (
    select
        a.uuid
        , a.naam
        , a.toestand
        , a.assettype
        , lookup.assetnaam
        , lookup.regexp_pattern
        , a.naam ~ lookup.regexp_pattern as naam_conform_naamconventie	 -- boolean check on regular expression
    from assets a
    inner join cte_lookup_table lookup on a.assettype = lookup.assettype
    where
        a.actief = true
        and a.naam is not null
    order by lookup.assetnaam asc, a.naam asc
    )
select * from cte_assets
where naam_conform_naamconventie is false
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
