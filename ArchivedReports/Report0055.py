from lib.reports.DQReport import DQReport


class Report0055:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0055',
                               title='Akela IMKL constraints for Pipe',
                               spreadsheet_id='1E235MT58snnRBuxsflMLJ2GMfWKqtR4PM6IXYCCVYjs',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
MATCH (x:IMKLPipe)
WITH x, [
//    {property: 'grp:currentStatus', value: x.`grp:currentStatus`, mandatory: true, enum: ['functional', 'projected', 'disused']},
//    {property: 'grp:inNetwork', value: x.`grp:inNetwork`, mandatory: true, enum: ['electricity', 'telecommunications', 'crossTheme']},
    {property: 'grp:containerType', value: x.`grp:containerType`, mandatory: true, enum: ['mantelbuis', 'kabelEnLeidingGoot']},
    {property: 'grp:kleur', value: x.`grp:kleur`, maxLength: 256},
    {property: 'grp:pipeDiameter', value: x.`grp:pipeDiameter`, mandatory: true, maxLength:256},
    {property: 'uuid', value: x.uuid, mandatory: true, maxLength: 255}
] AS checks
UNWIND checks AS check
WITH x, check.property AS property, check.value AS property_value, check.mandatory AS mandatory, check.enum AS enum, check.maxLength AS maxLength
WHERE 
    (mandatory = true AND property_value IS NULL) OR 
    (enum IS NOT NULL AND property_value IS NOT NULL AND NOT property_value IN enum) OR 
    (maxLength IS NOT NULL AND property_value IS NOT NULL AND size(toString(property_value)) > maxLength)
RETURN 
    x.uuid AS uuid,
    CASE 
        WHEN mandatory = true AND property_value IS NULL THEN 'is null/empty but mandatory'
        WHEN enum IS NOT NULL AND property_value IS NOT NULL AND NOT property_value IN enum THEN 'value not in enumeration'
        WHEN maxLength IS NOT NULL AND property_value IS NOT NULL AND size(property_value) > maxLength THEN 'max length exceeded'
    END AS fault,
    property,
	coalesce(property_value, 'NULL') as value
ORDER BY uuid, property;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
