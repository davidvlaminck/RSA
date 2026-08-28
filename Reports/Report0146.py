from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0146(BaseReport):
    def init_report(self) -> None:
        self.report = DQReport(name='report0146',
                               title='Dubbele bomen (Oost-Vlaanderen)',
                               spreadsheet_id='19vxyBuwy-JO3U3tCYNmrk2YXBEP8vO51oyGfvfb88sQ',
                               datasource='PostGIS',
                               persistent_column='T',
                               excel_filename='[RSA] Dubbele bomen (Oost-Vlaanderen).xlsx',
                               )

        self.report.result_query = """
with cte_gemeente as (
	select
		gemeente as naam_gemeente
		, niscode as nis
		, provincie as naam_provincie
		, geom as geometry
	from gemeente
	where
		provincie = 'Oost-Vlaanderen'
)
, cte_boom AS (
	SELECT
		a.uuid
		, a.toestand
		, a.actief
		, a.naam
		, w.waarde as soortnaam_origineel
		, l.geometry as geometry
		, l.ident2
		, l.ident8
	from assets a
	join locatie l on a.uuid = l.assetuuid
	join attribuutwaarden w on a.uuid = w.assetuuid
	where
		l.x > 77334 and l.x < 147307 and l.y > 156976 and l.y < 227141
		and
		a.assettype = 'cd77f043-dc69-46ae-98a1-da8443ca26bf'
		and
		a.actief = true
		and
		a.toestand = 'in-gebruik'
		and
		w.attribuutuuid = '27803bbe-ddf0-46c8-8107-130df29de615'
)
, cte_boom_incl_gemeente as (
	select
		boo.*
		, gem.naam_gemeente
		, gem.nis
		, gem.naam_provincie
	from cte_boom boo
	join cte_gemeente gem on st_DWithin(boo.geometry, gem.geometry, 0)
)
-- Main query
select
	b1.uuid as boom1_uuid
	, b1.ident2 as boom1_ident2
	, b1.ident8 as boom1_ident8
	, b1.naam as boom1_naam
	, b1.soortnaam_origineel as boom1_soortnaam_origineel
	, SUBSTRING(b1.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.soortnaamNederlands''\s*:\s*''([^'']*)''') as boom1_soortnaamNederlands
	, SUBSTRING(b1.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.soortnaamWetenschappelijk''\s*:\s*''([^'']*)''') as boom1_soortnaamWetenschappelijk
	, SUBSTRING(b1.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.wetenschappelijkeSoortnaam''\s*:\s*''([^'']*)''') as boom1_wetenschappelijkeSoortnaam
	, st_astext(b1.geometry) as boom1_geometry
	, ROUND(ST_Distance(b1.geometry, b2.geometry)::numeric, 3) as afstand
	, b2.uuid as boom2_uuid
	, b2.ident2 as boom2_ident2
	, b2.ident8 as boom2_ident8
	, b2.naam as boom2_naam
	, b2.soortnaam_origineel as boom2_soortnaam_origineel
	, SUBSTRING(b2.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.soortnaamNederlands''\s*:\s*''([^'']*)''') as boom2_soortnaamNederlands
	, SUBSTRING(b2.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.soortnaamWetenschappelijk''\s*:\s*''([^'']*)''') as boom2_soortnaamWetenschappelijk
	, SUBSTRING(b2.soortnaam_origineel FROM 'DtcVegetatieSoortnaam.wetenschappelijkeSoortnaam''\s*:\s*''([^'']*)''') as boom2_wetenschappelijkeSoortnaam
	, st_astext(b2.geometry) as boom2_geometry
from cte_boom_incl_gemeente b1
inner join cte_boom_incl_gemeente b2 on
	b1.nis = b2.nis
	and ST_DWithin(b1.geometry, b2.geometry, 1)
	and b1.uuid <> b2.uuid
order by b1.uuid, b2.uuid;
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
