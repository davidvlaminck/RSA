from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0224(BaseReport):
    def init_report(self) -> None:
        aql_query = """
/*
Report 0224: Laaspanningsbord heeft hoogstens 1 Elektrische Keuring met als toestand in-gebruik

Elektrische Keuring
Vertrekken vanuit het Laagspanningsbord (OTL)
  Relatie(s) naar Elektrische Keuring toevoegen
  Het aantal relaties met een Elektrische Keuring tellen en info toevoegen.

LEFT-JOIN toepassen, zodat alle Laagspanningsborden worden teruggegeven.

Laagspanningsbord -[HeeftKeuring]- Elektrische Keuring

Optimization: Instead of per-lsbord graph traversal (10K+ traversals
visiting ~197K vertices), scan HeeftKeuring edges once via relatietype_key
index (~7.8K edges), then look up source/destination vertices via DOCUMENT().
*/
LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)

/* Scan all HeeftKeuring edges using the relatietype_key persistent index */
LET all_edge_data = (
  FOR edge2 IN assetrelaties
    FILTER edge2.relatietype_key == key_relatie_heeftkeuring
    /* Look up source vertex (should be an active Laagspanningsbord) */
    LET lsbord = DOCUMENT(edge2._from)
    FILTER lsbord.assettype_key == key_laagspanningsbord AND lsbord.AIMDBStatus_isActief == true
    /* Look up destination vertex (should be an Elektrische Keuring) */
    LET elek_keuring = DOCUMENT(edge2._to)
    FILTER elek_keuring.assettype_key == key_elektrische_keuring
    FILTER elek_keuring.AIMDBStatus_isActief == true
    FILTER elek_keuring.toestand == 'in-gebruik'
    RETURN {
      lsbord_key: lsbord._key,
      lsbord_naam: lsbord.AIMNaamObject_naam,
      lsbord_naampad: lsbord.NaampadObject_naampad,
      lsbord_notitie: lsbord.AIMObject_notitie,
      keuring: {
        'assetId.identificator': elek_keuring._key,
        'typeURI': elek_keuring['@type'],
        'isActief': elek_keuring.AIMDBStatus_isActief,
        'toestand': SPLIT(elek_keuring.AIMToestand_toestand, '/')[-1],
        'naam': elek_keuring.AbstracteAanvullendeGeometrie_naam,
        'keuringsdatum': elek_keuring.KeuringObject_keuringsdatum,
        'resultaat': SPLIT(elek_keuring.ElektrischeKeuring_resultaat, '/')[-1],
        'eig_bijlage': elek_keuring.AbstracteAanvullendeGeometrie_bijlage,
        'eig_bijlage_uri': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_uri'] : null,
        'eig_bijlage_bestandsnaam': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_bestandsnaam'] : null,
        'eig_bijlage_omschrijving': elek_keuring.AbstracteAanvullendeGeometrie_bijlage != null ? elek_keuring.AbstracteAanvullendeGeometrie_bijlage['DtcDocument_omschrijving'] : null
      }
    }
)

/* Group keuringen per Laagspanningsbord */
FOR r IN all_edge_data
  COLLECT
    lsbord_key = r.lsbord_key,
    lsbord_naam = r.lsbord_naam,
    lsbord_naampad = r.lsbord_naampad,
    lsbord_notitie = r.lsbord_notitie
    INTO grouped
    LET elektrische_keuringen = (
      FOR g IN grouped
        SORT g.r.keuring['assetId.identificator']
        RETURN g.r.keuring
    )
  FILTER LENGTH(grouped) >= 1
  SORT LENGTH(grouped) DESC, lsbord_naam ASC
  RETURN {
    'lsbord.assetId.identificator': lsbord_key,
    'lsbord.naam': lsbord_naam,
    'lsbord.naampad': lsbord_naampad,
    'lsbord.commentaar': lsbord_notitie,
    'elektrische_keuringen_aantal': LENGTH(grouped),
    'elektrische_keuringen': elektrische_keuringen
  }
"""
        self.report = DQReport(name='report0224',
                               title='Laaspanningsbord heeft hoogstens 1 Elektrische Keuring met als toestand in-gebruik',
                               spreadsheet_id='9d58f5b5-ba90-4c74-ab1c-8b01303f5a2b',
                               datasource='ArangoDB',
                               persistent_column='G',
                               excel_filename='[RSA] Laaspanningsbord heeft hoogstens 1 Elektrische Keuring met als toestand in-gebruik.xlsx')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
