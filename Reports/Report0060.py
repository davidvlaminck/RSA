from DQReport import DQReport


class Report0060:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0060',
                               title='Er zijn geen conflicten tussen EAN-nummers (dubbel EAN-nummer).',
                               spreadsheet_id='1od9125ZSoFG6fGwvoS8CSCz-Bne4N8vVBXORjYhtjQY',
                               datasource='Neo4J',
                               persistent_column='I',
                               link_type='eminfra')

        self.report.result_query = """
            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) 
            WHERE ((y:DNBHoogspanning) OR (y:DNBLaagspanning)) AND  x.eanNummer <> y.eanNummer
            RETURN 
                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, 
                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,
                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie
            UNION 
            MATCH (x:Asset{isActief: True})-[:HoortBij]-(y{isActief: True}) 
            WHERE (y:DNBHoogspanning) OR (y:DNBLaagspanning)
            WITH x, count(DISTINCT y.eanNummer) as ean_count 
            WHERE ean_count > 1
            RETURN 
                x.uuid as uuid, x.naampad as naampad, x.toestand as toestand, 
                x.`tz:toezichter.tz:voornaam` as tz_voornaam, x.`tz:toezichter.tz:naam` as tz_naam, x.`tz:toezichter.tz:email` as tz_email,
                x.`tz:toezichtgroep.tz:naam` as tzg_naam,  x.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# rapport om te vormen naar EAN nummers zijn uniek binnen DNBHoogspanning en DNBLaagspanning
# forfaitaire aansluitingen moeten niet worden meegenomen (staat nog niet in de query)
aql_query = """
LET dnb_keys = (
  FOR at IN assettypes
    FILTER at.short_uri IN ["onderdeel#DNBHoogspanning","onderdeel#DNBLaagspanning"]
    RETURN at._key
)

LET duplicateEans = (
  FOR a IN assets
    FILTER a.AIMDBStatus_isActief == true
      AND a.DNB_eanNummer != null
      AND a.DNB_eanNummer != ""
    COLLECT ean = a.DNB_eanNummer WITH COUNT INTO cnt
    FILTER cnt > 1
    RETURN ean
)

FOR d IN assets
  FILTER
    d.AIMDBStatus_isActief == true
    AND d.assettype_key IN dnb_keys
    AND d.DNB_eanNummer IN duplicateEans

  LET toezichter = FIRST(
    FOR v, e IN 1..1 OUTBOUND d._id betrokkenerelaties
      FILTER e.rol == "toezichter"
      RETURN v.purl.Agent_naam
  )
  
  SORT d.DNB_eanNummer ASC, d._key ASC

  RETURN DISTINCT {
    uuid:        d._key,
    naam:        d.AIMNaamObject_naam,
    ean:         d.DNB_eanNummer,
    toestand:    d.toestand,
    toezichter:  toezichter ? toezichter : null
  }
"""