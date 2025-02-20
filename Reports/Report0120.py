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
select
    a.uuid
    , at.uri
    , a.naampad
    , a.naam
    , a.commentaar 
FROM assets a
left join assettypes at on a.assettype = at.uuid
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
    and
    a.assettype not in (
        'efb995df-057b-4ab8-baa8-4f9918f8ec5e'  -- fietstelinstallatie
        , '8d42ee56-17d3-455e-bd9c-1eb1aad3c1ec'  -- fietsteldisplay
        , 'c0def180-e2a5-40eb-abdd-c752cbab48af'  -- fietstelsysteem
        , '7a175f2f-d195-4fb6-bdb3-84f398629e39'  -- zoutbijlaadplaats
        , 'c575f03c-83c1-41c0-9dc6-3d1232bebe99'  -- silo
        , 'cdcd6d8b-0e73-4f87-a62d-be8744e075db'  -- tank
    )
    and not
    (a.assettype = 'f8da675c-eadc-412e-99bc-de25912c6d07'  -- nietselectievedetectielus
     and a.naam like '%fiets%')
    ;
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
