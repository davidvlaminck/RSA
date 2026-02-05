from lib.reports.DQReport import DQReport


class Report0154:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0154',
                               title='Dubbele Straatkolken (Limburg)',
                               spreadsheet_id='16EmsvsSgwCXfJ7HXmVCXaFIw58yVoqVQReyWZV09xzc',
                               datasource='PostGIS',
                               persistent_column='J'
                               )

        self.report.result_query = """
/*
 * Alle Straatkolken, met aanduiding van ident2, ident8 en de dubbele Straatkolken binnen een afstand van X meter 
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
--		provincie = 'West-Vlaanderen'
--		provincie = 'Oost-Vlaanderen'
--		provincie = 'Vlaams-Brabant'
--		provincie = 'Antwerpen'
		provincie = 'Limburg'
)
, cte_straatkolk AS (
	SELECT
		a.uuid
		, l.geometry as geometry
		, l.ident2
		, l.ident8
	from assets a
	left join locatie l on a.uuid = l.assetuuid
	where
--		l.x > 21991 and l.x < 90411 and l.y > 155928 and l.y < 229725  -- BBOX extent West-Vlaanderen
--		l.x > 77334 and l.x < 147307 and l.y > 156976 and l.y < 227141  -- BBOX extent Oost-Vlaanderen
--		l.x > 116098 and l.x < 207630 and l.y > 153058 and l.y < 193542  -- BBOX extent Vlaams-Brabant
--		l.x > 136231 and l.x < 212520 and l.y > 186679 and l.y < 244028  -- BBOX extent Antwerpen
		l.x > 192882 and l.x < 258872 and l.y > 154162 and l.y < 221731 -- BBOX extent Limburg
		and
		a.assettype = 'a5c7c355-c073-4f31-8e77-389c4b7a6a9e' -- Straatkolk
		and
		a.actief = true
		and
		a.toestand = 'in-gebruik'
		and
		l.geometry is not null
)
, cte_straatkolk_incl_gemeente as (
	select
		str.*
		, gem.naam_gemeente
		, gem.nis
		, gem.naam_provincie
	from cte_straatkolk str
	-- Gebruik niet de bounding box intersection (&&), noch de werkelijke intersection ST_Intersection(geom, geom)
	-- Het meest performant is de functie ST_Dwithin met een bufferafstand van 0 meter.
	-- Voorwaarde is dat er een spatial index bestaat.
	left join cte_gemeente gem on st_DWithin(str.geometry, gem.geometry, 0) where gem.nis is not null
)
-- Main query
--select * from cte_straatkolk_incl_gemeente;
select
	s1.uuid as straatkolk1_uuid
	, s1.ident2 as straatkolk1_ident2
	, s1.ident8 as straatkolk1_ident8
	, st_astext(s1.geometry) as straatkolk1_geometry
	, ROUND(ST_Distance(s1.geometry, s2.geometry)::numeric, 3) as afstand
	, s2.uuid as straatkolk2_uuid
	, s2.ident2 as straatkolk2_ident2
	, s2.ident8 as straatkolk2_ident8
	, st_astext(s2.geometry) as straatkolk2_geometry
-- Join een Straatkolk met zichzelf
from cte_straatkolk_incl_gemeente s1
--left join cte_straatkolk_incl_gemeente s2 on  -- left join: alle straatkolken, de vrijstaande en de dubbele
inner join cte_straatkolk_incl_gemeente s2 on  -- inner join: enkel de dubbele straatkolken, niet de vrijstaande
	s1.naam_provincie = s2.naam_provincie  -- beide straatkolken binnen dezelfde provincie
	and s1.nis = s2.nis -- beide straatkolken binnen dezelfde gemeente
    -- and s1.geometry && s2.geometry -- bbox intersection check
	-- De bufferafstand tussen 2 Straatkolken is kleiner dan een gegeven afstand (te bepalen)
	and ST_DWithin(s1.geometry, s2.geometry, 1.0)   -- Exact distance check. Beide Straatkolken binnen een straal van x meter van elkaar
	and s1.uuid <> s2.uuid  -- geen vergelijking van een straatkolk met zichzelf
order by s1.uuid, s2.uuid;
        
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
