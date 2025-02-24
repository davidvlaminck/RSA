from DQReport import DQReport


class Report0179:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0179', title='Assets gelinkt aan bestekken zonder aannemer',
                               spreadsheet_id='1KoN2tfOLSmJJ6OT540hyIwkf3MXX6vrnnLkONS-nIis', datasource='PostGIS',
                               persistent_column='L')

        self.report.result_query = """
with cte_bestek_zonder_aannemer as (
	select uuid as bestekuuid, edeltadossiernummer, edeltabesteknummer, aannemernaam
	from bestekken
	where aannemernaam is null
)
select
	a."uuid"
	, a.assettype
	, a.toestand
	, a.actief 
	, a.naampad 
	, a.naam
	, bk.koppelingstatus
	, b.bestekuuid
	, b.edeltadossiernummer
	, b.edeltabesteknummer
	, b.aannemernaam
from assets a
left join bestekkoppelingen bk on a.uuid = bk.assetuuid 
left join cte_bestek_zonder_aannemer b on bk.bestekuuid = b.bestekuuid
where
	bk.koppelingstatus = 'actief'
	and
	b.bestekuuid is not null
--	and 
--	a."uuid" = 'af795ae4-33d8-43f5-a5c5-fc5576866d45'
order by b.bestekuuid, toestand
	    """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
