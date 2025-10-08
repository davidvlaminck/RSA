from DQReport import DQReport


class Report0201:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0201',
                               title='Naamgeving overzicht',
                               spreadsheet_id='1VNme4tAQ0KJ5TZpyK3DikNfX7yftgCeKM6y8VLvEc9g',
                               datasource='PostGIS',
                               persistent_column='J',
                               link_type='eminfra')

        self.report.result_query = """
/*
 * Query1
 * UPSERT bestaande of nieuwe assettypes in tabel regex
 * */
INSERT INTO regex (uri, pattern, description, validated)
VALUES ('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Laagspanningsbord', '^.*.LSB\d*$', 'Suffix .LSB, optioneel gevolgd door digits', false)
ON CONFLICT(uri)
DO UPDATE SET
  uri = EXCLUDED.uri,
  pattern = EXCLUDED.pattern,
  description = EXCLUDED.description,
  validated = EXCLUDED.validated
;
INSERT INTO regex (uri, pattern, description, validated)
VALUES ('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Wegkantkast', '^.*.K\d*$', 'Suffix .K, optioneel gevolgd door digits', false)
ON CONFLICT(uri)
DO UPDATE SET
  uri = EXCLUDED.uri,
  pattern = EXCLUDED.pattern,
  description = EXCLUDED.description,
  validated = EXCLUDED.validated
;
INSERT INTO regex (uri, pattern, description, validated)
VALUES ('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#HSCabine', '^.*.HS\d*$', 'Suffix .HS, optioneel gevolgd door digits', false)
ON CONFLICT(uri)
DO UPDATE SET
  uri = EXCLUDED.uri,
  pattern = EXCLUDED.pattern,
  description = EXCLUDED.description,
  validated = EXCLUDED.validated
;


/*
 * Query2
 * UPDATE de aantallen
 * */
with cte_assettypes as (
	select r.uri, at."uuid", at.naam, r.pattern  -- zorgen dat de later juiste assets gelezen kunnen worden 
	from regex r
	left join assettypes at on r.uri = at.uri
), 
cte_assets as ( -- selection of only the right assets 
	select 
		at.naam,
		a.naam as ass_naam, 
		a.uuid, 
		at.uuid as assettype, 
		at.pattern,
		at.uri as uri_assettype
	from cte_assettypes at
	inner join assets a on at.uuid = a.assettype
	where a.actief = true
--		and a.einddatum is null
	), 
correct as ( -- counting the amount of assets that follow the right regex; grouped by the assettype
	select 
		a.uri_assettype,
		count(*) as count_correct
	from cte_assets a
	where a.ass_naam ~ a.pattern
	group by a.uri_assettype
), 
wrong as ( -- counting the amount of assets that have a value but do not follow the right regex; grouped by the assettype
	select 
		a.uri_assettype, 
		count(*) as count_wrong
	from cte_assets a  
	where a.ass_naam !~ a.pattern and a.naam is not null
	group by a.uri_assettype
), 
empty as ( -- counting the amount of assets that dont have a value; grouped by the assettype
	select 
		a.uri_assettype, 
		count(*) as count_empty 
	 from cte_assets a 
	 where a.ass_naam is null
	 group by a.uri_assettype
), 
combined as( -- samenzetten van de verschillende updated count nummers
	select 
		at.uri, 
		coalesce(a.count_correct, 0) as count_correct,
		coalesce(b.count_wrong, 0) as count_wrong,
		coalesce(c.count_empty, 0) as count_empty
	from cte_assettypes at
	left join correct a on at.uri = a.uri_assettype
	left join wrong b on at.uri = b.uri_assettype
	left join empty c on at.uri = c.uri_assettype
)
update regex -- updating the regex table with the counts of before 
set 
	count_valid = c.count_correct, 
	count_null = c.count_empty, 
	count_invalid = c.count_wrong
from combined c
where regex.uri = c.uri


/*
 * Query3
 * Selecteer de aantallen voor een overzicht
 * */
select
	uri
	, pattern as "regex patroon"
	, description "beschrijving"
	, count_null as "aantal_null"
	, count_valid as "aantal_geldig"
	, count_invalid "aantal_ongeldig"
	, count as "aantal_totaal"
	, updated_at
	, validated as "naamgeving gevalideerd door AWV"
from regex 
            """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
