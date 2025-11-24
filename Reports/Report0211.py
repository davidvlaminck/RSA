from DQReport import DQReport


class Report0211:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0211',
                               title='Dubbele niet-gerichte relatie tussen assets',
                               spreadsheet_id='1AztJXPe2irCDmu3dJuRB9TMvCXOrU-y9qnrnFR4vnhg',
                               datasource='PostGIS',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
            with rel as (
                select
                    rel.*
                    , case
                        when rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20' then 'Bevestiging'
                        when rel.relatietype = '93c88f93-6e8c-4af3-a723-7e7a6d6956ac' then 'Sturing'
                    end as "relatie"
                from assetrelaties rel
                where rel.relatietype in (
                    '3ff9bf1c-d852-442e-a044-6200fe064b20'  -- Bevestiging
                    , '93c88f93-6e8c-4af3-a723-7e7a6d6956ac'  -- Sturing
                )
            )
            -- main query
            select
                -- bron asset
                rel1.bronuuid
                , a1.naam
                -- doel asset
                , rel1.doeluuid
                , a2.naam
                , rel1.relatie 
            from rel rel1
            inner join rel rel2 on rel1.bronuuid = rel2.doeluuid and rel1.doeluuid = rel2.bronuuid and rel1.relatietype = rel2.relatietype 
            -- koppel info van de assets aan de relatie
            inner join assets a1 on rel1.bronuuid = a1."uuid" and a1.actief is true 
            inner join assets a2 on rel1.doeluuid = a2."uuid" and a2.actief is true
            order by rel1.relatie, rel1."bronuuid";
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
