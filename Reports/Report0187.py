from DQReport import DQReport


class Report0187:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0187', title='Toezichtsgroepen bevatten geen Legacy-assets: AWV_EW_AN; AWV_EW_VB; AWV_EW_OW; AWV_EW_WV; AWV_EW_LB',
                               spreadsheet_id='1R4M4Q4dPXeEh4kvnu8sN_EcfX2DNdvV2VsU6kCuQA7k', datasource='PostGIS',
                               persistent_column='G', link_type='eminfra')

        self.report.result_query = """
        with cte_toezichtsgroep as (
            select
                t.uuid, t.naam
            from toezichtgroepen t
            where t.uuid in (
                '2006554d-745e-4cf7-9560-6e9c135cae24' -- Antwerpen
                , 'e9eb3b87-e9a4-44fc-b4bc-c37d046f949f'  -- Limburg
                , 'd2258b3e-b6bc-4a3c-a87f-c5cd17d67b97'  -- Oost-Vlaanderen
                , '02c16d19-42f9-4cd2-9ff1-7faf86cc1eb7'  -- Vlaams-Brabant
                , 'b2bcd6af-ae91-4d72-9bb9-a16bdf489ca7'  -- West-Vlaanderen
            )
        )
        -- main query
        select
            a."uuid"
            , at.naam as assettype
            , a.naampad 
            , a.naam 
            , a.actief 
            , t.naam
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        inner join cte_toezichtsgroep t on a.toezichtgroep = t.uuid
        where a.actief is true
        order by assettype asc;
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
