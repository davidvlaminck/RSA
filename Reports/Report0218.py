from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0218(BaseReport):
    def init_report(self) -> None:
        aql_query = """
 LET at_dnblaagspanning = FIRST(FOR at IN assettypes FILTER at.label == "DNBLaagspanning" LIMIT 1 RETURN at._key)
 LET at_dnbhoogspanning = FIRST(FOR at IN assettypes FILTER at.label == "DNBHoogspanning" LIMIT 1 RETURN at._key)
 LET at_hsbeveiligingscel = FIRST(FOR at IN assettypes FILTER at.label == "HSBeveiligingscel" LIMIT 1 RETURN at._key)
 LET at_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.label == "Laagspanningsbord" LIMIT 1 RETURN at._key)
 LET at_hscabine = FIRST(FOR at IN assettypes FILTER at.label == "HSCabine" LIMIT 1 RETURN at._key)
 LET at_segmentcontroller = FIRST(FOR at IN assettypes FILTER at.label == "Segmentcontroller" LIMIT 1 RETURN at._key)
 LET at_ab = FIRST(FOR at IN assettypes FILTER at.short_uri == "lgc:installatie#AB" LIMIT 1 RETURN at._key)

FOR a IN assets
FILTER
  a.AIMDBStatus_isActief == true AND a.assettype_key IN [ at_dnblaagspanning, at_dnbhoogspanning, at_hsbeveiligingscel, at_laagspanningsbord, at_hscabine, at_segmentcontroller, at_ab ] AND a.geometry == null

LET assettype = FIRST(FOR at IN assettypes FILTER at._key == a.assettype_key LIMIT 1 RETURN at)
LET toezichter = FIRST(FOR t IN identiteiten FILTER t._key == a.toezichter_key LIMIT 1 RETURN t)
LET toezichtgroep = FIRST(FOR tg IN identiteiten FILTER tg._key == a.toezichtgroep_key LIMIT 1 RETURN tg)

SORT a.NaampadObject_naampad ASC

RETURN 
  {
    uuid: a._key, 
    assettype: assettype ? assettype.label : null,
    toestand: a.toestand, 
    naampad: a.NaampadObject_naampad, 
    naam: a.AIMNaamObject_naam,
    toezichter: toezichter.voornaam && toezichter.naam ? concat(toezichter.voornaam, " ", toezichter.naam) : null,
    toezichtgroep: toezichtgroep.naam
  } 
"""
        self.report = DQReport(name='report0218',
                               title='Locatie ontbreekt voor voeding-assets (LS, LSDeel, HS, HSDeel, HSCabine, SegmentController, Afstandsbewaking)',
                               spreadsheet_id='1wxPYC35mwexrhWDEX6FQ_xcr_ZdLX6D4PY0g11nwl1U',
                               datasource='ArangoDB',
                               persistent_column='G',
                               link_type='eminfra',
                               excel_filename='[RSA] Locatie ontbreekt voor voeding-assets (LS, LSDeel, HS, HSDeel, HSCabine, SegmentController, Afstandsbewaking).xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
