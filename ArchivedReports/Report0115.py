from DQReport import DQReport


class Report0115:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0115',
                               title='EAN Nummer is steeds ingevuld (Legacy-data)',
                               spreadsheet_id='1dZBo960siYL8u9UZSigp_Ql7SIeFWPx-NYTdPNvnPzs',
                               datasource='PostGIS',
                               persistent_column='F',
                               link_type='eminfra')

        self.report.result_query = """
        select
            a.uuid
            , at.uri
            , a.naampad
            , a.naam
            , ea.aansluiting
        from elek_aansluitingen ea
        left join assets a on ea.assetuuid = a."uuid" 
        left join assettypes at on a.assettype = at."uuid" 
        where
            ea.ean is null
            and
            a.actief = true 
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
