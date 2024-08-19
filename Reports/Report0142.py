from DQReport import DQReport


class Report0142:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0142',
                               title='Dubbele Aanvullende Geometrie',
                               spreadsheet_id='124_Y-L0kp2pM67TY6jL4M1eHfZBl_6Nh8xFyFYnhK30M',
                               datasource='PostGIS',
                               persistent_column='F'
                               )

        self.report.result_query = """
            /*
            Wanneer spreken we van dubbels?
            Bevragen dubbele asset Aanvullende Geometrie.
            Is die dubbel zodra de naam identiek is (#311), zodra de geometrie identiek is (#982) of zodra de naam en de geometrie identiek zijn (#76)?
            Alles in totaal zijn er een 1369 assets.
            */
            with cte_aanvullendegeometrie_dubbelenaam as (
                select
                    min(a.uuid::text) as uuid
                    , count(a.naam) as aantal
                    , string_agg(a.uuid::text, '; ') as uuid_agg
                    , string_agg(a.naam::text, '; ') as naam_agg
                from assets a 
                where
                    a.actief = true
                    and
                    a.assettype = 'afdeacf2-c21a-4ac4-9ee7-70bebe794638'  -- Aanvullende Geometrie
                group by a.naam
                having count(a.naam) > 1
                order by count(a.naam) desc
            )
            ,
            cte_aanvullendegeometrie_dubbelegeometrie as (
                select
                    min(a.uuid::text) as uuid
                    -- g.wkt_string
                    , count(g.wkt_string) as aantal
                    , string_agg(g.assetuuid::text, '; ') as uuid_agg
                    , string_agg(a.naam, '; ') as naam_agg
                from assets a
                left join geometrie g on a.uuid = g.assetuuid
                where
                    a.actief = true
                    and
                    a.assettype = 'afdeacf2-c21a-4ac4-9ee7-70bebe794638'  -- Aanvullende Geometrie
                group by g.wkt_string
                having count(g.wkt_string) > 1
                order by count(g.wkt_string) desc
            )
            ,
            cte_aanvullendegeometrie_dubbelenaam_dubbelegeometrie as (
                select
                    min(a.uuid::text) as uuid
                    --, g.wkt_string
                    , count(g.wkt_string) as aantal
                    , string_agg(a.uuid::text, '; ') as uuid_agg
                    , string_agg(a.naam::text, '; ') as naam_agg
                from assets a
                left join geometrie g on a.uuid = g.assetuuid
                where
                    a.actief = true
                    and
                    a.assettype = 'afdeacf2-c21a-4ac4-9ee7-70bebe794638'  -- Aanvullende Geometrie
                group by g.wkt_string, a.naam
                having count(g.wkt_string) > 1
                order by count(g.wkt_string) desc
            )
            -- Main query
            select *, 'identieke naam' as type_dubbel from cte_aanvullendegeometrie_dubbelenaam
            union
            select *, 'identieke geometrie' as type_dubbel from cte_aanvullendegeometrie_dubbelegeometrie
            union
            select *, 'identieke naam én geometrie' as type_dubbel from cte_aanvullendegeometrie_dubbelenaam_dubbelegeometrie
            order by aantal desc, uuid asc
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
