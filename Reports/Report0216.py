from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0216(BaseReport):
    def init_report(self) -> None:
        aql_query = """
LET assettype_uuids = [
  "efb995df-057b-4ab8-baa8-4f9918f8ec5e",  /* fietstelinstallatie */
  "8d42ee56-17d3-455e-bd9c-1eb1aad3c1ec",  /* fietsteldisplay */
  "c0def180-e2a5-40eb-abdd-c752cbab48af",  /* fietstelsysteem */
  "7a175f2f-d195-4fb6-bdb3-84f398629e39",  /* zoutbijlaadplaats */
  "cdcd6d8b-0e73-4f87-a62d-be8744e075db",  /* tank */
  "c575f03c-83c1-41c0-9dc6-3d1232bebe99",  /* silo */
  "27db1214-a622-45f8-b124-384598b210f4",  /* ASTRID installatie */
  "9baa5c87-a56e-4ece-9fd0-a0d82a3dc7ec",  /* Radioheruitzend installatie */
  "3ff63fb2-0234-4e94-a807-5db4dd05a92e",  /* ITSapp */
  "ae45eec9-b992-4704-a3df-11e8d65d2ad1",  /* Meteostation */
  "4749ba74-ed5a-4811-9428-bcf0e227093a",  /* Elektromotor */
  "a88493ab-3748-4636-96ed-9c8e8460260d",  /* Toegangscontroller */
  "4e12c432-1546-4bbd-95d9-8fc9bc1e0e02",  /* MIV Meetpunt */
  "7f59b64e-9d6c-4ac9-8de7-a279973c9210",  /* MIV-module */
  "b6f86b8d-543d-4525-8458-36b498333416",  /* Netwerkelement */
  "50f7400a-2e67-4550-b135-08cde6f6d64f",  /* DynBordVMS */
  "0515e9bc-1778-43ae-81a9-44df3e2b7c21",  /* DynBordRVMS */
  "4aabd323-5480-4771-b33f-28d5c6d46cee",  /* DynBordPK */
  "fcc947c6-5923-4d56-96fc-73ce4b0bae7f",  /* DynBordGroep */
  "87ef5c66-1f50-4010-a47c-90027ad72421",  /* Hoogtedetectie */
  "9826b683-02fa-4d97-8680-fbabc91a417f",  /* DynBordRSS */
  "40b2e487-f4b8-48a2-be9d-e68263bab75a",  /* Seinbrug */
  "615356ae-64eb-4a7d-8f40-6e496ec5b8d7",  /* Galgpaal */
  "6d7544da-2688-4e87-b9e1-305a9009ba18",  /* Z30Groep */
  "4afb0d67-bf8f-4e0e-8544-6af1f296f6bf",  /* DynBordZ30 */
  "8d9f83fa-0e19-47ec-902f-ac2c538dd6d9",  /* Lichtmast */
  "6d518126-d229-4446-89ee-1ae2a9be4318",  /* Stralende Kabel */
  "48afe679-1483-46dd-ac5e-b3f2f97506bf",  /* Zuil toegangscontrole */
  "7044685e-dfdb-421c-9825-2c268b7d2e2f",  /* Dynamisch Bord Externe Processing Unit */
  "79ecb22b-e1ff-4032-a95b-a33c69d15135",  /* Cabine */
  "3f98f53a-b435-4a69-af3c-cede1cd373a7",  /* Camera */
  "788e72fa-24b8-4f4c-8ed7-d8448c9cd76f",  /* Cameragroep */
  "30a173e5-bb95-4391-b533-99adcdba033c",  /* Omvormer */
  "6e61fb1c-ebff-49e2-8fe0-45fc24626991",  /* Power over Ethernet (PoE) Injector */
  "052aa583-f54c-4f03-9c17-09995bb28a5d",  /* Illuminator */
  "df9f19eb-5eb3-49d9-b782-6b22cfb8993b",  /* Bel */
  "be55ecdf-aa99-4dac-b00a-6ad4f9f6b615",  /* Calamiteitendoorsteek */
  "99c0e9c3-0aea-4648-86b4-45a16a5a5ee4",  /* Calamiteitendoorsteekgroep */
  "0f55b669-2b77-4812-ae6f-867749fc76ac",  /* Slagboom */
  "bf2b7871-47ec-468c-93ba-7a2833389b3e",  /* Slagboomgroep */
  "2c73932c-fa50-4677-89fb-778393263488",  /* Kokerafsluiting */
  "d5705624-233f-4e05-9574-86dd9c98b4e5",  /* Hulppost */
  "c7d996a9-00e2-4ddf-af81-3f7eb76cbc8a",  /* Hulppostgroep */
  "a58ed6fe-e930-41b4-baa4-b7f7950b5b3b",  /* Inwenvig verlicht pictogram */
  "c3106313-4b66-44cb-b885-39ae91fdf00e",  /* Brandblusser */
  "86dc2408-ff32-42a7-a393-718a5f9fcf91",  /* Luchtkwaliteit zender ontvanger */
  "07f28457-3123-4bd8-baee-8504c027d358",  /* Luchtkwaliteitsensor */
  "9cb182d9-d893-43e4-b998-09cd950bccd5",  /* Noodverlichtingstoestel */
  "42efc21e-8424-4680-a611-d0f04d2a215c",  /* Intercomtoestel */
  "664a09b8-ce64-49a1-9cc4-b575ab072095",  /* Intercomserver */
  "d3e26758-6b3d-4ee9-b04e-238eefe86e43",  /* Deur */
  "cf53f4fd-a8ca-413a-83c4-1c670fab7a5e",  /* Contourverlichting */
  "6e9010da-507f-426c-a4c5-f3a49baacb8a",  /* Kokerventilatie */
  "f815c084-ac38-4f9b-8bc3-a501ef6c227f",  /* Ventilatiecluster */
  "69462525-65de-4951-8442-57cbc24fe598",  /* Ventilator */
  "f11afc31-c780-4630-a5e4-7147abb4987a",  /* Ventilatie afsluitklep */
  "015f6cc2-7daa-4578-a360-01c810feaff6",  /* Tunneluitrusting */
  "10088403-228d-43f7-9aa6-66469d2e7760",  /* Pomp */
  "3d6b7eca-e4d6-40bd-ba98-1059efcba670",  /* Drukverhogingsgroep */
  "e889caba-ad57-43e1-8b1a-7ad3b11dd57a",  /* Gassensor */
  "fe26c074-edf3-4307-a4dc-1a9c18001325",  /* Lichtsensor */
  "d9904200-b625-433f-8f3e-2eb8d5db091c",  /* Luchtkwaliteitssensor */
  "fbf9755a-5f67-4dc9-9637-03331aa0780b",  /* Tunnelverlichting */
  "217ba1cb-43a7-464c-a968-ac2582e45207",  /* Flitsgroep */
  "4cd16712-1ee7-460f-9729-08da0c87e947",  /* Flitspaal */
  "3e8bd99a-8e6f-4653-aab4-b5be694ccb10",  /* Flitscamera */
  "47777ce0-09c3-42ca-a9bb-a685717ace57",  /* UitleesapparatuurFlitscamera */
  "d93fb220-f0e5-40cd-9f5d-2416140cb19e",  /* DynBordOpMaat */
  "ba0e8976-aff6-43d6-8c3e-db65f096f251",  /* BiFlash */
  "800f0a16-773c-473e-82a3-e471a3c7246f",  /* BiFlashInstallatie */
  /* verweving Q1 2026 */
  "",  /* Asweger */
  "",  /* Aswegersite */
  "",  /* Gebouwuitrusting */
  "",  /* Gebouw */
  "",  /* Lokaal */
  "",  /* Wegkantkast */
  "",  /* Laagspanningsbord */
  "",  /* DNB laagspanning */
  /* verweving Q2 2026 */  
  "",  /* Wegverlichting groep */
  "",  /* Verlichte oversteekplaats groep */
  "",  /* Segmentcontroller */
  "",  /* Cabinecontroller */
  "",  /* DNB hoogspanning */
  "",  /* HS-cabine */
  "",  /* HS beveiligingscel */
  "",  /* HS melder */
  "",  /* LS schuif */
  "",  /* Algemeen LaagSpanningsBord */
  "",  /* Transformator */
  "",  /* Asweger */
  "",  /* Pompstation */
  "",  /* Geleidingsverlichting */
  "",  /* Deur */
  "",  /* Waze beacon */

  
  /* verweving Q2 2026 (in overleg met Edison) */
/*  "478add39-e6fb-4b0b-b090-9c65e836f3a0",  /* WVLichtmast */ 
/*  "e78ce094-565b-4e8c-a956-88c105367a4f",  /* WVConsole */
/*  "12b2af6b-72e1-4028-b6ed-3d3b654735d4",  /* WVBevestigd */
/*  "622ac17d-2ea7-46bb-9c36-c47794404ef2",  /* Punctuele verlichtingsmast */
  /* overige */
  "e67900b1-88fb-44da-9285-409f7f67147f"   /* BinnenverlichtingGroep */
]

LET assettype_keys = (
  FOR uuid IN assettype_uuids
    RETURN SUBSTRING(uuid, 0, 8)
)

FOR a IN assets
  FILTER a.AIMDBStatus_isActief == true
  FILTER a.NaampadObject_naampad == null OR a.NaampadObject_naampad == ""
  FILTER a.assettype_key IN assettype_keys

  LET assettype = FIRST(
    FOR at IN assettypes
      FILTER at._key == a.assettype_key
      LIMIT 1
      RETURN at
  )

  SORT a.NaampadObject_naampad ASC, a.AIMNaamObject_naam ASC

  RETURN {
    uuid: a._key,
    asset_status: a.AIMDBStatus_isActief,
    naam: a.AIMNaamObject_naam,
    naampad: a.NaampadObject_naampad,
    uri: assettype ? assettype.uri : null,
    label: assettype ? assettype.label : null,
    assettype_status: assettype ? assettype.actief : null
  }
"""
        self.report = DQReport(name='report0216',
                               title='Verweven assets hebben geen naampad (zijn niet in een boomstructuur op EM-infra gesitueerd)',
                               spreadsheet_id='17MTZ2N_jVsUyc53zbzPwFGhDS8u1X6xrrexU-Li-OkU',
                               datasource='ArangoDB',
                               persistent_column='H',
                               link_type='eminfra',
                               excel_filename='[RSA] Verweven assets hebben geen naampad.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
