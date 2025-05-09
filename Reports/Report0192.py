from DQReport import DQReport


class Report0192:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0192', title='Overzicht van het aantal Bezoekt-relaties per bron- en doelassettype',
                               spreadsheet_id='1vcrJrrS3kXC4hiP9QiDY2WbxCm40CwCW_nEKCP4Q55o', datasource='PostGIS',
                               persistent_column='D', link_type='eminfra')

        self.report.result_query = """
        with cte_bezoek_relaties as (
            select 
                rel."uuid"
                , 'Bezoekt' as "relatie"
                , rel.actief 
                , a1.naam as bron_naam
                , at1.uri as bron_assettype
                , a2.naam as doel_naam
                , at2.uri as doel_assettype
            from assetrelaties rel
            left join assets a1 on rel.bronuuid = a1.uuid
            left join assets a2 on rel.doeluuid = a2.uuid
            left join assettypes at1 on a1.assettype = at1.uuid
            left join assettypes at2 on a2.assettype = at2.uuid
            where
                rel.relatietype = 'e801b062-74e1-4b39-9401-163dd91d5494' -- relatie: Bezoekt
                and rel.actief is true
        )
        -- main query
        select
            bron_assettype
            , doel_assettype
            , count(*) as aantal
        from cte_bezoek_relaties
        group by bron_assettype, doel_assettype
        order by doel_assettype asc
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
