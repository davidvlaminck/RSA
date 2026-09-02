from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0231(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /*
Report0231
Laagspanningsbord heeft een behuizing (Wegkantkast/HSCabine/...)
*/
LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
LET key_wegkantkast = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Wegkantkast' LIMIT 1 RETURN at._key)
LET key_hscabine = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#HSCabine' LIMIT 1 RETURN at._key)
LET key_derdenobject = FIRST(FOR at IN assettypes FILTER at.short_uri == 'implementatieelement#Derdenobject' LIMIT 1 RETURN at._key)
LET key_gebouw = FIRST(FOR at IN assettypes FILTER at.short_uri == 'installatie#Gebouw' LIMIT 1 RETURN at._key)
LET key_lokaal = FIRST(FOR at IN assettypes FILTER at.short_uri == 'installatie#Lokaal' LIMIT 1 RETURN at._key)
LET key_cabine = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Cabine' LIMIT 1 RETURN at._key)
LET key_container = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Container' LIMIT 1 RETURN at._key)
LET key_hulppostkast = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Hulppostkast' LIMIT 1 RETURN at._key)
LET key_technischeput = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#TechnischePut' LIMIT 1 RETURN at._key)
LET key_relatie_bevestiging = FIRST(FOR rel_type IN relatietypes FILTER rel_type.naam == 'Bevestiging' LIMIT 1 RETURN rel_type._key)

/* List of asset types to check for Bevestiging-relatie */
LET allowed_asset_types = [key_wegkantkast, key_hscabine, key_derdenobject, key_gebouw, key_lokaal, key_cabine, key_container, key_hulppostkast, key_technischeput]

/* Pre-filter all active Laagspanningsborden */
FOR lsbord IN assets
  FILTER lsbord.assettype_key == key_laagspanningsbord
  FILTER lsbord.AIMDBStatus_isActief == true
  FILTER lsbord.toestand IN ['in-gebruik']

  /* Check if there are NO Bevestiging relationships with the allowed asset types */
  LET has_bevestiging = LENGTH(
    FOR v, e IN 1..1 ANY lsbord assetrelaties
      FILTER e.relatietype_key == key_relatie_bevestiging
      FILTER v.AIMDBStatus_isActief == true
      FILTER v.assettype_key IN allowed_asset_types
      RETURN 1
  )
  FILTER has_bevestiging == 0

  /* Pre-fetch toezichter and toezichtsgroep in a single traversal */
  LET betrokkenen = (
    FOR v, e IN 1..1 OUTBOUND lsbord betrokkenerelaties
      FILTER e.rol IN ['toezichter', 'toezichtsgroep']
      RETURN { rol: e.rol, agent: v }
  )

  /* Extract toezichter and toezichtsgroep from betrokkenen */
  LET toezichter = FIRST(FOR b IN betrokkenen FILTER b.rol == 'toezichter' RETURN b.agent)
  LET toezichtsgroep = FIRST(FOR b IN betrokkenen FILTER b.rol == 'toezichtsgroep' RETURN b.agent)

  RETURN {
  'lsbord.assetId.identificator': lsbord._key,
	'lsbord.naam': lsbord.AIMNaamObject_naam,
	'lsbord.naampad': lsbord.NaampadObject_naampad,
	'toezichter': toezichter.purl.Agent_naam ? toezichter.purl.Agent_naam : null,
  'toezichtsgroep': toezichtsgroep.purl.Agent_naam ? toezichtsgroep.purl.Agent_naam : null,
  }
        """

        self.report = DQReport(name='report0231',
                               title='Laagspanningsbord heeft een behuizing',
                               datasource='ArangoDB',
                               persistent_column='F',
                               link_type='eminfra',
                               excel_filename='[RSA] Laagspanningsbord heeft een behuizing.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
