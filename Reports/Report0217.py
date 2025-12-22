from DQReport import DQReport


class Report0217:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0217',
                               title='Toezichtsgroep ontbreekt voor voeding-assets (LS, LSDeel, HS, HSDeel, HSCabine)',
                               spreadsheet_id='1d1OEDsFjaDU11mIi7J5CVVx-UTiP8p0A5VmIO03YuO0',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
            with cte_assets_voeding as (
                select
                    a.*
                from assets a
                where
                    a.actief is true
                    and
                    a.assettype in (
                        '80fdf1b4-e311-4270-92ba-6367d2a42d47', -- Laagspanningsaansluiting (Legacy)
                        'b4361a72-e1d5-41c5-bfcc-d48f459f4048', -- Laagspanningsgedeelte (Legacy)
                        '46dcd9b1-f660-4c8c-8e3e-9cf794b4de75', -- Hoogspanning (Legacy)
                        'a9655f50-3de7-4c18-aa25-181c372486b1', -- Hoogspanningsgedeelte (Legacy)
                        '1cf24e76-5bf3-44b0-8332-a47ab126b87e' -- Hoogspanningscabine (Legacy)
                    )
            )
            -- main query
            select
                a."uuid",
                at."label" as assettype,
                a.toestand,
                a.naampad, 
                a.naam,
                t.voornaam || ' ' || t.naam as "toezichter_naam"
            from cte_assets_voeding a
            left join assettypes at on a.assettype = at."uuid"
            left join identiteiten t on a.toezichter = t.uuid
            where a.toezichtgroep is null
            order by a.naampad
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
