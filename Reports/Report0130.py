from DQReport import DQReport


class Report0130:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0130',
                               title='Geometrie Linestring heeft identieke eindpunten en bevat meer dan 2 punten',
                               spreadsheet_id='1sbY-T8UZqE-tau7Hu6860OLXjNQ0wuDC5AI-yov35NY',
                               datasource='PostGIS',
                               persistent_column='E'
                               )

        self.report.result_query = """
            -- Report0130
            with cte_asset_of_interest as (
                select
                    a.uuid
                    , at.label as assettype_label
                    , st_geomfromtext(g.wkt_string) as geom
                    , st_npoints(st_geomfromtext(g.wkt_string)) as npoints 
                from assets a
                left join geometrie g on a.uuid = g.assetuuid
                left join assettypes at on a.assettype = at.uuid
                where g.wkt_string ~ '^LINESTRING*'
                  and at.uri !~ '^https://lgc.data.*'
                  and at.label not in (
                    'Aardingskabel'
                    , 'Beschermbuis'
                    , 'Datakabel'
                    , 'ElectricityCable'
                    , 'Gracht'
                    , 'IMKLElectricityCable'
                    , 'IMKLExtraPlan'
                    , 'IMKLPipe'
                    , 'IMKLTelecomCable'
                    , 'KabelnetBuis'
                    , 'MIVLus'
                    , 'NietSelectieveDetectielus'
                    , 'Onderdoorboring'
                    , 'OverlangseMarkering'
                    , 'SelectieveDetectielus'
                    , 'Signaalkabel'
                    , 'Telecomkabel'
                    , 'TelecommunicationsCable'
                    , 'Voedingskabel'
                  )
            )
            select
                uuid
                , assettype_label
                , left(st_astext(geom), 100) as wkt_geom_afgerond
                , npoints
            from cte_asset_of_interest
            where
                npoints > 2 -- Linestring consists of more than 2 points
                and
                st_pointn(geom, 1) = st_pointn(geom, -1) -- Endpoints of the linestring are identical
            order by assettype_label asc
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
