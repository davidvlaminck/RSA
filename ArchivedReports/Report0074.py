from lib.reports.LegacyHistoryReport import LegacyHistoryReport


class Report0074:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = LegacyHistoryReport(name='report0074',
                                          title="Datcleaning van verkeersregelaar uit VRI script",
                                          spreadsheet_id='',
                                          datasource='Neo4j',
                                          persistent_column='C')

        self.report.result_query = """
        CALL {
            MATCH (vregelaar:Verkeersregelaar)
            WHERE 
                (vregelaar.`loc:puntlocatie.loc:adres.loc:gemeente` IS NULL) 
                AND (vregelaar.`loc:puntlocatie.loc:weglocatie.loc:gemeente` IS NULL)
            RETURN vregelaar, 'geen gemeente gevonden onder adres en weglocatie' AS data_cleaning_fout
            UNION
            MATCH (vregelaar:Verkeersregelaar)
            WHERE 
                vregelaar.`loc:puntlocatie.loc:adres.loc:provincie` IS NULL
            RETURN vregelaar, 'geen provincie gevonden onder adres' AS data_cleaning_fout
            UNION
            MATCH (vregelaar:Verkeersregelaar)
            WHERE
                (vregelaar.`loc:geometrie` IS NULL) AND
                (vregelaar.`geo:log[0].geo:geometrie.geo:punt` IS NULL)
            RETURN vregelaar, 'geen coördinaten gevonden onder locatie en geometrie' as data_cleaning_fout
        }
        WITH vregelaar.uuid AS uuid, collect(data_cleaning_fout) AS data_cleaning_fouten
        RETURN uuid, data_cleaning_fouten
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
