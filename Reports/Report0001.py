from DQReport import DQReport


class Report0001:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0001',
                               title='Onderdelen hebben een HoortBij relatie',
                               spreadsheet_id='16iUSRuS9M85P4E7Mi5-1J8pWgPr6Ehp1liEmRaZFNi4',
                               datasource='PostGIS',
                               persistent_column='D')

        # TODO feedback: bevestigingsbeugel en omvormer weghalen (omvormer naar camera moet wel aanwezig zijn)
        self.report.result_query = """
            with cte_netwerkpoort_netwerkkaart as (
                -- assets die een bevestiging-relatie hebben met een Netwerkpoort of Netwerkkaart
                -- # 9671
                select
                    a1.*
                from assets a1
                inner join assetrelaties rel on a1.uuid = rel.bronuuid and rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'  -- Bevestiging
                inner join assets a2 on rel.doeluuid = a2.uuid and a2.assettype = 'b6f86b8d-543d-4525-8458-36b498333416' -- Netwerkelement
                where
                    a1.actief is true
                    and a2.actief is true
                    and a1.assettype in ('6b3dba37-7b73-4346-a264-f4fe5b796c02', '0809230e-ebfe-4802-94a4-b08add344328')  -- Netwerkpoort, Netwerkkaart
                union
                -- # 41757
                select
                    a1.*
                from assets a1
                inner join assetrelaties rel on a1.uuid = rel.doeluuid and rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'  -- Bevestiging
                inner join assets a2 on rel.bronuuid = a2.uuid and a2.assettype = 'b6f86b8d-543d-4525-8458-36b498333416' -- Netwerkelement
                where
                    a1.actief is true 
                    and a2.actief is true
                    and a1.assettype in ('6b3dba37-7b73-4346-a264-f4fe5b796c02', '0809230e-ebfe-4802-94a4-b08add344328')  -- Netwerkpoort, Netwerkkaart
            )
            , cte_relatie_hoortbij as (
                -- Actieve relaties van het type "HoortBij"
                select
                    r.*
                    , bron_assettype.label as bron_assettype
                    , bron_asset.naam AS bron_naam
                    , doel_assettype.label as doel_assettype
                    , doel_asset.naam AS doel_naam
                from assetrelaties r
                left join assets bron_asset on r.bronuuid = bron_asset.uuid
                left join assettypes bron_assettype on bron_asset.assettype = bron_assettype.uuid
                left join assets doel_asset on r.doeluuid = doel_asset.uuid
                left join assettypes doel_assettype on doel_asset.assettype = doel_assettype.uuid
                where
                    r.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'  -- HoortBij
                    and
                    r.actief = true
                    and
                    bron_asset.actief = true
                    and
                    doel_asset.actief = true
            )
            ,
            cte_onderdelen AS (
                select
                        a.*
                    from assets a
                    left join assettypes at on a.assettype = at.uuid
                    where
                        a.actief = true
                        and
                        at.uri ~ '^https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#'
            )
            -- main query
            select
                ond.uuid
                , ond.naam
                , at.uri as typeURI
            from cte_onderdelen ond
            left join assettypes at on ond.assettype = at.uuid
            left join cte_relatie_hoortbij rel_bron on ond.uuid = rel_bron.bronuuid
            left join cte_relatie_hoortbij rel_doel on ond.uuid = rel_doel.bronuuid
            left join cte_netwerkpoort_netwerkkaart netwerkpoort_kaart on ond.uuid = netwerkpoort_kaart.uuid
            where
                rel_bron.uuid is null  -- geen bestaande HoortBij-relatie vertrekkend vanuit het onderdeel
                and
                rel_doel.uuid is null -- geen bestaande HoortBij-relatie die toekomt in het onderdeel
                and 
                netwerkpoort_kaart.uuid is null  -- uuid is not in the cte-table cte_netwerkpoort_netwerkkaart
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
