from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0223(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        /* 
        Report0223: Laagspanningsbord heeft minstens 1 Elektrische Keuring
        
        Vertrekken vanuit het Laagspanningsbord (OTL)
          Relatie(s) naar Elektrische Keuring toevoegen
          Het aantal relaties met een Elektrische Keuring tellen en info toevoegen.
          
        Laagspanningsbord -[HeeftKeuring]- Elektrische Keuring 
        
        */
        LET key_elektrische_keuring = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#ElektrischeKeuring' LIMIT 1 RETURN at._key)
        LET key_laagspanningsbord = FIRST(FOR at IN assettypes FILTER at.short_uri == 'onderdeel#Laagspanningsbord' LIMIT 1 RETURN at._key)
        LET key_relatie_heeftkeuring = FIRST(FOR rel_type in relatietypes FILTER rel_type.naam == 'HeeftKeuring' LIMIT 1 RETURN rel_type._key)
        
        
        // Pre-compute the cardinality (number of assets per lsbord)
        LET lsbordCardinality = (
          FOR lsbord IN assets
            FILTER lsbord.assettype_key == key_laagspanningsbord
            LET assetCount = LENGTH(
              FOR asset, edge IN 1..1 OUTBOUND lsbord assetrelaties
                FILTER edge.relatietype_key == key_relatie_heeftkeuring
                RETURN asset
            )
            RETURN { [lsbord._key]: assetCount }
        )
        LET lsbordCardinality_lookup = MERGE(lsbordCardinality)
        
        
        /* Alle Laagspanningsborden */
        FOR lsbord IN assets
          FILTER lsbord.assettype_key == key_laagspanningsbord and lsbord.AIMDBStatus_isActief == true
        
          // Lookup the cardinality for the current lsbord
          LET elektrische_keuringen_aantal = lsbordCardinality_lookup[lsbord._key]
          FILTER elektrische_keuringen_aantal == 0
          
          SORT lsbord.AIMNaamObject_naam asc
        
          RETURN {
            'lsbord.assetId.identificator': lsbord._key,
            'lsbord.toestand': lsbord.toestand,
            'lsbord.naam': lsbord.AIMNaamObject_naam,
            'lsbord.naampad': lsbord.NaampadObject_naampad,
            'elektrische_keuringen_aantal': elektrische_keuringen_aantal,
          }
        """
        self.report = DQReport(name='report0223',
                               title='Laagspanningsbord heeft minstens 1 Elektrische Keuring ',
                               spreadsheet_id='',
                               datasource='ArangoDB',
                               persistent_column='E')

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
