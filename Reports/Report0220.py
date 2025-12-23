from DQReport import DQReport


class Report0220:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0220',
                               title='EAN-nummer ontbreekt (assettypes: DNBLaagspanning en DNBHoogspanning)',
                               spreadsheet_id='1ZLoygJt-wIiOLOcRtk8s1xDDAX-nrSpGvtSjEW99Lq0',
                               datasource='PostGIS',
                               persistent_column='F',
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
		a.naam
	from assets a
	left join attribuutwaarden aw ON a.uuid = aw.assetuuid AND aw.attribuutuuid = 'a108fc8a-c522-4469-8410-62f5a0241698' -- eanNummer
	where
		a.assettype in ('b4ee4ea9-edd1-4093-bce1-d58918aee281', '8e9307e2-4dd6-4a46-a298-dd0bc8b34236') -- DNBLaagspanning & DNBHoogspanning 
		and
		a.actief = true
		and
		aw.waarde is null)
-- main query
select * from cte_assets_eannummer;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
