from DQReport import DQReport


class Report0052:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0052',
                               title='Akela IMKL constraints for ElectricityCable',
                               spreadsheet_id='1bCiwfYJxEbYQ8fd3AcL61SwCdGZaLVW9xNkKOagNzRg',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """
        MATCH (x:IMKLElectricityCable)
        WITH x, [
            {property: 'grp:currentStatus', value: x.`grp:currentStatus`, mandatory: true, enum: ['functional', 'projected', 'disused']},
            {property: 'grp:inNetwork', value: x.`grp:inNetwork`, mandatory: true, enum: ['electricity', 'telecommunications', 'crossTheme']},
            {property: 'grp:kleur', value: x.`grp:kleur`, maxLength: 256},
            {property: 'grp:nominalVoltage', value: x.`grp:nominalVoltage`, mandatory: true},
            {property: 'grp:operatingVoltage', value: x.`grp:operatingVoltage`, mandatory: true},
            {property: 'grp:subThema', value: x.`grp:subThema`, mandatory: true, enum: ['elektriciteitTransport', 'elektriciteitTransportPlaatselijk', 'elektriciteitDistributieHoogspanning', 'elektriciteitDistributieLaagspanning', 'elektriciteitOpenbareVerlichting', 'elektriciteitVerkeerslichten', 'elektriciteitVerkeershandhavingssystemen']},
            {property: 'uuid', value: x.uuid, mandatory: true, maxLength: 255}
        ] AS checks
        UNWIND checks AS check
        WITH x, check.property AS property, check.value AS property_value, check.mandatory AS mandatory, check.enum AS enum, check.maxLength AS maxLength
        WHERE 
            (mandatory = true AND property_value IS NULL) OR 
            (enum IS NOT NULL AND property_value IS NOT NULL AND NOT property_value IN enum) OR 
            (maxLength IS NOT NULL AND property_value IS NOT NULL AND size(property_value) > maxLength)
        RETURN 
            x.uuid AS uuid,
            CASE 
                WHEN mandatory = true AND property_value IS NULL THEN 'is null/empty but mandatory'
                WHEN enum IS NOT NULL AND property_value IS NOT NULL AND NOT property_value IN enum THEN 'value not in enumeration'
                WHEN maxLength IS NOT NULL AND property_value IS NOT NULL AND size(property_value) > maxLength THEN 'max length exceeded'
            END AS fault,
            property + "_" + coalesce(property_value, 'NULL') as property_and_value
        ORDER BY uuid, property;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
