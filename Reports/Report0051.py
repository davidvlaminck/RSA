from DQReport import DQReport


class Report0051:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0051',
                               title='Akela IMKL constraints for Appurtenance (ElectricityAppurtenance and TelecomAppurtenance have seperate IMKL no types)',
                               spreadsheet_id='1YFBTA9LDACfW5IV1wBT-T6OQFkhi6i6bwpduppYoals',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
MATCH (x:IMKLAppurtenance)
WITH x, [
    {property: 'grp:currentStatus', value: x.`grp:currentStatus`, mandatory: true, enum: ['functional', 'projected', 'disused']},
    {property: 'grp:inNetwork', value: x.`grp:inNetwork`, mandatory: true, enum: ['electricity', 'telecommunications', 'crossTheme']},
    {property: 'grp:appurtenanceType', value: x.`grp:appurtenanceType`, mandatory: true, enum: ['aarding','mof','deliveryPoint','streetLight','spliceClosure','termination']},
    {property: 'grp:subThema', value: x.`grp:subThema`, mandatory: true, enum: ['elektriciteitTransport','elektriciteitTransportPlaatselijk','elektriciteitDistributieHoogspanning','elektriciteitDistributieLaagspanning','elektriciteitOpenbareVerlichting','elektriciteitVerkeerslichten','elektriciteitVerkeershandhavingssystemen','elektronischeCommunicatie']},
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
    property,
	coalesce(property_value, 'NULL') as value
ORDER BY uuid, property;
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
