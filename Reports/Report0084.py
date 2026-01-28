from DQReport import DQReport


class Report0084:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='Report0084',
                               title='Verkeersregelaars hebben een vplannummer en vplandatum dat overeenkomt met het legacy vplan',
                               spreadsheet_id='1pGZUOMXLeWRo0Ykzshxt9PJN2tCbznsBxQf0mgh7Zos',
                               datasource='PostGIS',
                               persistent_column='H')

        self.report.result_query = """
WITH vr_otl AS (
	select
		a.uuid, 
		a.naam,
		vplandatum.waarde::timestamptz AS vplandatum,
		vplannummer.waarde AS vplannummer 
	FROM assets a
	LEFT JOIN attribuutwaarden vplandatum ON vplandatum.assetuuid = a.uuid AND vplandatum.attribuutuuid = 'c8f6b633-efba-4124-838b-805ae9a82c5a'
	LEFT JOIN attribuutwaarden vplannummer ON vplannummer.assetuuid = a.uuid AND vplannummer.attribuutuuid = 'b943728d-d69d-4425-a4eb-db50989d9923'
	WHERE actief = TRUE AND assettype = '3d24792a-6941-481b-9c8c-739309fd3ffb')
,
vr_lgc AS (
select uuid, naam, vplannummer, indienstdatum 
from (
	select
		a."uuid",
		a.naam,
		vpl.vplannummer,
		vpl.indienstdatum,
		ROW_NUMBER() OVER (
            PARTITION BY a.uuid
            ORDER BY vpl.indienstdatum DESC
        ) AS row_number
	FROM assets a
	left join vplan_koppelingen vpl ON vpl.assetuuid = a.uuid
	where
		a.actief = true
		AND a.assettype = '13fa9473-f919-432a-bd00-bc19645bd30a'
		and vpl.uitdienstdatum IS null
	)
where row_number = 1
)
-- main query
select
	-- LGC attributen
	vr_lgc.uuid as "lgc_uuid",
	vr_lgc.naam as "lgc_naam",
	vr_lgc.vplannummer as "lgc_vplannummer",
	vr_lgc.indienstdatum as "lgc_indienstdatum",
	-- OTL attributen
	vr_otl.uuid as "otl_uuid",
	vr_otl.naam as "otl_naam",
	vr_otl.vplannummer as "otl_vplannummer",
	vr_otl.vplandatum as "otl_vplandatum"
FROM vr_lgc vr_lgc
	LEFT JOIN assetrelaties rel ON vr_lgc.uuid = rel.doeluuid AND rel.relatietype = '812dd4f3-c34e-43d1-88f1-3bcd0b1e89c2'
	LEFT JOIN vr_otl vr_otl on rel.bronuuid = vr_otl.uuid
where
	(
	vr_lgc.vplannummer is not null
	and
	vr_lgc.indienstdatum IS not null
	)
	and
	vr_otl.uuid is not null
	or
	(lower(vr_otl.vplannummer) <> lower(vr_lgc.vplannummer))
	or
	(vr_otl.vplandatum <> vr_lgc.indienstdatum)
"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
