from DQReport import DQReport


class Report0120:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0120',
                               title='OTL installatie types mogen niet voorkomen in "legacy" boomstructuren',
                               spreadsheet_id='1sBJEGOpcGfrjvBWGAkBU_vnWirsGwq2cL8faX3vdapI',
                               datasource='PostGIS',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
            WITH otl_installatietypes as (
                SELECT uuid, naam, label, uri
                FROM assettypes a
                WHERE uri LIKE '%installatie%' AND NOT uri LIKE '%lgc%'
                )
            select
                a.uuid
                , at.uri
                , a.naampad
                , a.naam
                , a.commentaar 
            FROM assets a
            left join assettypes at on a.assettype = at.uuid
            where
                a.assettype IN (SELECT uuid FROM otl_installatietypes)
                and
                a.actief = true
                and
                a.naampad NOT LIKE 'DA-%'  -- Davie
                and
                a.naampad NOT LIKE 'OTN.%' -- Optisch Transport Netwerk
                and
                a.naampad NOT LIKE 'Netwerkgroepen%';
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
