from DQReport import DQReport


class Report0214:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0214',
                               title='Laagspanning (LS) is nergens aan bevestigd',
                               spreadsheet_id='1VaF3IRiF5lFOkh_hK4_PvTqYanhiaRzvJX_lqmWbn3g',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a1."uuid" as "ls_uuid", 
                at1.label as "ls_label",
                a1.actief as "ls_actief",
                a1.naam as "ls_naam", 
                a1.naampad as "ls_naampad",
                'Geen Bevestiging-relatie aanwezig' as "relatie"
            from assets a1
            left join assettypes at1 on a1.assettype = at1.uuid
            where
                a1.actief is true
                and
                a1.assettype = '80fdf1b4-e311-4270-92ba-6367d2a42d47'  -- Laagspanningsaansluiting (Legacy)
                and
                a1.uuid not in (
                    select rel.bronuuid from assetrelaties rel where rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'
                )
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
