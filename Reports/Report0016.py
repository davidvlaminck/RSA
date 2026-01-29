from DQReport import DQReport


class Report0016:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET netwerkpoort_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkpoort" LIMIT 1 RETURN at._key)
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)
LET netwerkkaart_key   = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkkaart" LIMIT 1 RETURN at._key)

FOR p IN assets
  FILTER p.assettype_key == netwerkpoort_key
  FILTER p.AIMDBStatus_isActief == true
  FILTER p.AIMNaamObject_naam != null

  LET has_bevestiging = LENGTH(
    FOR other, rel IN ANY p bevestiging_relaties
      FILTER (other.assettype_key == netwerkelement_key OR other.assettype_key == netwerkkaart_key)
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_bevestiging

  RETURN {
    uuid: p._key,
    naam: p.AIMNaamObject_naam
  }
"""
        self.report = DQReport(name='report0016',
                               title='Netwerkpoorten hebben een Bevestiging relatie met een Netwerkelement of een Netwerkkaart',
                               spreadsheet_id='16NJCwhrHnYuz6Z9leqGswfOR0bt7EdBK_GonPB-3y7o',
                               datasource='ArangoDB',
                               persistent_column='C')

        self.report.result_query = aql_query
        self.report.cypher_query = """WITH poorten AS (\n\tSELECT * \n\tFROM assets \n\tWHERE assettype = '6b3dba37-7b73-4346-a264-f4fe5b796c02' AND actief = true\n\tand naam is not null\n\t), -- Netwerkpoort\nrelaties AS (\n\tSELECT assetrelaties.uuid, \n\t\tCASE WHEN bron.uuid IS NOT NULL THEN doeluuid\n\t\t\tWHEN doel.uuid IS NOT NULL THEN bronuuid\n\t\t\tELSE NULL END AS bron_uuid \n\tFROM assetrelaties\n\t\tLEFT JOIN assets bron ON assetrelaties.bronuuid = bron.uuid AND bron.actief = TRUE AND bron.assettype IN ('b6f86b8d-543d-4525-8458-36b498333416', '0809230e-ebfe-4802-94a4-b08add344328') -- Netwerkelement/Netwerkkaart\n\t\tLEFT JOIN assets doel ON assetrelaties.doeluuid = doel.uuid AND doel.actief = TRUE AND doel.assettype IN ('b6f86b8d-543d-4525-8458-36b498333416', '0809230e-ebfe-4802-94a4-b08add344328') -- Netwerkelement/Netwerkkaart\n\tWHERE relatietype = '3ff9bf1c-d852-442e-a044-6200fe064b20' -- Bevestiging\n\t\tAND (bron.uuid IS NOT NULL OR doel.uuid IS NOT NULL))\nselect\n\tpoorten.uuid,\n\tpoorten.naam,\n\tpoorten.actief\nFROM poorten\n\tLEFT JOIN relaties ON poorten.uuid = relaties.bron_uuid\nWHERE relaties.uuid IS NULL;"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
