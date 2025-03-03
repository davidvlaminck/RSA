from DQReport import DQReport


class Report0181:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0181', title='Wetenschappelijke notaties komen niet voor',
                               spreadsheet_id='1GDwzQP9TxQuMDc6_B57tx8ct_gjkoTQhvNQcil5iETo', datasource='PostGIS',
                               persistent_column='G', link_type='eminfra')

        self.report.result_query = """
        SELECT 
            a.uuid
            , at.naam as assettype
            , a.naam
            , a.naampad
            , attr.naam as attribuutnaam
            , aw.waarde AS attribuutwaarde
        FROM assets a
        LEFT JOIN attribuutwaarden aw on a.uuid = aw.assetuuid
        left join attributen attr on aw.attribuutuuid = attr."uuid"
        LEFT JOIN assettypes at on a.assettype = at."uuid" 
        WHERE a.actief IS TRUE 
            AND aw.waarde IS NOT NULL
            AND aw.waarde ~* '^\d{1}.\d*e\+\d+$'
        order by assettype, naampad, naam
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
