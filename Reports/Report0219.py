from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0219(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0219',
                               title='Identieke (niet-unieke) EAN-nummers bij meerdere assets (assettypes: DNBLaagspanning en DNBHoogspanning)',
                               spreadsheet_id='1gUDGRCTpwUK-ygXBigM0Jeyo05RpbKhiGWsEzL0MWgk',
                               datasource='PostGIS',
                               persistent_column='H',
                               link_type='eminfra')

        self.report.result_query = """
with cte_assets_eannummer as (
	select
		a.uuid,
		case
			when a.assettype = 'b4ee4ea9-edd1-4093-bce1-d58918aee281' then 'DNBLaagspanning'
			when a.assettype = '8e9307e2-4dd6-4a46-a298-dd0bc8b34236' then 'DNBHoogspanning'
		end as "assettype",
		a.actief,
		a.toestand,
		a.naam,
		aw.waarde as eanNummer	
	from assets a
	left join attribuutwaarden aw ON a.uuid = aw.assetuuid AND aw.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698' -- eanNummer
	where
		a.assettype in ('b4ee4ea9-edd1-4093-bce1-d58918aee281', '8e9307e2-4dd6-4a46-a298-dd0bc8b34236') -- DNBLaagspanning & DNBHoogspanning 
		and
		a.actief = true
		and
		aw.waarde is not null),
cte_assets_eannummer_aantallen as (
	select
		a.*,
		count(a.*) over (partition by a.eannummer) as aantal
	from cte_assets_eannummer a
)
-- main query
select *
from cte_assets_eannummer_aantallen
where aantal > 1
order by aantal desc, eannummer asc, toestand
    """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
