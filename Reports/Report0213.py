from lib.reports.DQReport import DQReport


class Report0213:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0213',
                               title='Laagspanning (LS) is bevestigd aan een Kast (Legacy)',
                               spreadsheet_id='1JK1zb3RP-mwDgcbenxjfSAcbWjCrMaq0vluRdhKIwQs',
                               datasource='PostGIS',
                               persistent_column='L',
                               link_type='eminfra')

        self.report.result_query = """
            select
                a1."uuid" as "ls_uuid", 
                at1.label as "ls_label",
                a1.actief as "ls_actief",
                a1.naam as "ls_naam", 
                a1.naampad as "ls_naampad",
                'Bevestiging-relatie aanwezig' as "relatie",
                a2."uuid",
                at2."label",
                a2.actief,
                a2.naam,
                a2.naampad
            from assets a1
            left join assettypes at1 on a1.assettype = at1.uuid
            left join assetrelaties rel on a1."uuid" = rel.bronuuid and rel.relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20'  -- Bevestiging
            left join assets a2 on rel.doeluuid = a2.uuid
            left join assettypes at2 on a2.assettype = at2.uuid
            where
                a1.actief is true
                and
                a2.actief is true
                and
                rel.actief is true
                and
                a1.assettype = '80fdf1b4-e311-4270-92ba-6367d2a42d47'  -- Laagspanningsaansluiting (Legacy)
                and
                a2.assettype not in (
                    '10377658-776f-4c21-a294-6c740b9f655e'  -- Kast (Legacy)
                )
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
