from DQReport import DQReport


class Report0145:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0145',
                               title='Dubbele bomen (West-Vlaanderen)',
                               spreadsheet_id='1rqDPhMkGU1Y0gwOoJ6HHHaH055hu0DNSaAZOXp3896w',
                               datasource='PostGIS',
                               persistent_column='T'
                               )

        self.report.result_query = """
/*
 * Alle bomen, met aanduiding van ident2, ident8 en de dubbele bomen binnen een afstand van X meter 
 * Deactiveer in 2 Common Table Expressions (CTE) 4 provincies.
 * */
with cte_gemeente as (
	select
		gemeente as naam_gemeente
		, niscode as nis
		, provincie as naam_provincie
		, geom as geometry
	from gemeente
	where
		provincie = 'West-Vlaanderen'
		--provincie = 'Oost-Vlaanderen'
		--provincie = 'Vlaams-Brabant'
		--provincie = 'Antwerpen'
		--provincie = 'Limburg'
)
, cte_boom AS (
	SELECT
		a.uuid
		, a.toestand
		, a.actief
		, a.naam
		, w.waarde as soortnaam_origineel
		-- Convert JSON5 to JSON
		-- De keys worden omsloten door enkele weglatingstekens
		-- De values worden omsloten door enkele ofwel dubbele weglatingstekens.
		-- Standaard worden enkele weglatingstekens gebruikt.
		-- Indien de value zelf weglatingstekens bevat, worden dubbele gebruikt om de value te omsluiten.
		-- Gebruik de replace-functie nested om volgende karakter sequenties te vervangen
		-- ': '  ': " 
		-- ', '  ", '
		-- {'  }'  '{  '}
		-- ""
		, replace(
			replace(
				replace(
					replace(
						replace(
							replace(
								replace(
					    			replace(
					    				replace(
					    					REPLACE(
					        					w.waarde
					        					-- enkel weglatingsteken dubbelpunt spatie enkel weglatingsteken
					            				, ''': '''
					            				, '": "')
				            				-- enkel weglatingsteken dubbelpunt spatie dubbel weglatingsteken
											, ''': "'
											, '": "')
										-- enkel weglatingsteken komma spatie enkel weglatingsteken
										, ''', '''
										, '", "')
									-- dubbel weglatingsteken komma spatie enkel weglatingsteken
									, '", '''
									, '", "')
								-- sluit curly bracket enkel weglatingsteken
			            		, '}'''
								, '}"')
							-- open curly bracket enkel weglatingsteken
		            		, '{'''
		            		, '{"')
	            		-- enkel weglatingsteken sluit curly-bracket
						, '''}'
						, '"}')
					-- enkel weglatingsteken open curly-bracket
					, '''{'
					, '"{')
				-- dubbel weglatingsteken
				, '""'
				, '"')
			-- dubbel weglatingsteken (nogmaals)
			, '""'
			, '"')
			as soortnaam
		, l.geometry as geometry
		, l.ident2
		, l.ident8
	from assets a
	left join geometrie g ON a.uuid = g.assetuuid
	left join locatie l on a.uuid = l.assetuuid
	left join attribuutwaarden w on a.uuid = w.assetuuid
	where
		l.x > 21991 and l.x < 90411 and l.y > 155928 and l.y < 229725  -- BBOX extent West-Vlaanderen
--		l.x > 77334 and l.x < 147307 and l.y > 156976 and l.y < 227141  -- BBOX extent Oost-Vlaanderen
--		l.x > 116098 and l.x < 207630 and l.y > 153058 and l.y < 193542  -- BBOX extent Vlaams-Brabant
--		l.x > 136231 and l.x < 212520 and l.y > 186679 and l.y < 244028  -- BBOX extent Antwerpen
--		l.x > 192882 and l.x < 258872 and l.y > 154162 and l.y < 221731 -- BBOX extent Limburg
		and
		a.assettype = 'cd77f043-dc69-46ae-98a1-da8443ca26bf' -- Boom
		and
		a.actief = true
		and
		a.toestand = 'in-gebruik'
		and
		w.attribuutuuid = '27803bbe-ddf0-46c8-8107-130df29de615' -- soortnaam
)
, cte_boom_incl_gemeente as (
	select
		boo.*
		, gem.naam_gemeente
		, gem.nis
		, gem.naam_provincie
	from cte_boom boo
	-- Gebruik niet de bounding box intersection (&&), noch de werkelijke intersection ST_Intersection(geom, geom)
	-- Het meest performant is de functie ST_Dwithin met een bufferafstand van 0 meter.
	-- Voorwaarde is dat er een spatial index bestaat.
	left join cte_gemeente gem on st_DWithin(boo.geometry, gem.geometry, 0) where gem.nis is not null
)
-- Main query
--select * from cte_boom_incl_gemeente;
select
	b1.uuid as boom1_uuid
	, b1.ident2 as boom1_ident2
	, b1.ident8 as boom1_ident8
	, b1.naam as boom1_naam
	, b1.soortnaam_origineel as boom1_soortnaam_origineel
    , b1.soortnaam::json->>'DtcVegetatieSoortnaam.soortnaamNederlands' AS boom1_soortnaamNederlands
	, b1.soortnaam::json->>'DtcVegetatieSoortnaam.soortnaamWetenschappelijk' AS boom1_soortnaamWetenschappelijk
	, b1.soortnaam::json->>'DtcVegetatieSoortnaam.wetenschappelijkeSoortnaam' AS boom1_wetenschappelijkeSoortnaam
	, st_astext(b1.geometry) as boom1_geometry
	, ROUND(ST_Distance(b1.geometry, b2.geometry)::numeric, 3) as afstand
	, b2.uuid as boom2_uuid
	, b2.ident2 as boom2_ident2
	, b2.ident8 as boom2_ident8
	, b2.naam as boom2_naam
	, b2.soortnaam_origineel as boom2_soortnaam_origineel
    , b2.soortnaam::json->>'DtcVegetatieSoortnaam.soortnaamNederlands' AS boom2_soortnaamNederlands
	, b2.soortnaam::json->>'DtcVegetatieSoortnaam.soortnaamWetenschappelijk' AS boom2_soortnaamWetenschappelijk
	, b2.soortnaam::json->>'DtcVegetatieSoortnaam.wetenschappelijkeSoortnaam' AS boom2_wetenschappelijkeSoortnaam
	, st_astext(b2.geometry) as boom2_geometry
-- Join een boom met zichzelf
from cte_boom_incl_gemeente b1
--left join cte_boom_incl_gemeente b2 on  -- left join: alle bomen, de vrijstaande en de dubbele
inner join cte_boom_incl_gemeente b2 on  -- inner join: enkel de dubbele bomen, niet de vrijstaande
	--b1.naam_provincie = b2.naam_provincie  -- beide bomen binnen dezelfde provincie
	--and
	b1.nis = b2.nis -- beide bomen binnen dezelfde gemeente
    and b1.geometry && b2.geometry -- bbox intersection check
	-- De bufferafstand tussen 2 bomen is kleiner dan een gegeven afstand (te bepalen)
	and ST_DWithin(b1.geometry, b2.geometry, 1)   -- Exact distance check. Beide bomen binnen een straal van x meter van elkaar
	and b1.uuid <> b2.uuid  -- geen vergelijking van een boom met zichzelf
order by b1.uuid, b2.uuid;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
