from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0123(BaseReport):
    def init_report(self) -> None:
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
                , 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geleideconstructie'
                , 'https://grp.data.wegenenverkeer.be/ns/installatie#IMKLPipe'
                , 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Beschermbuis'
                , 'https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KabelnetBuis'
            )
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
            st_area(st_orientedenvelope(st_setsrid(st_geomfromtext(g.wkt_string), 31370))) > 10000000
        )
        -- main query
        select uuid, naam, uri, oppervlakte
        from cte_assets_met_oppervlakte
        where 
            -- groter dan 10 vierkante kilometer
            oppervlakte > 10000000
        order by naam asc, oppervlakte desc        
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
