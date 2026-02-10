from lib.reports.DQReport import DQReport


class Report0056:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0056',
                               title='Akela IMKL constraints for TelecomCable',
                               spreadsheet_id='1ZL2eJVB9mqByJnUcryqknPsGFCZhhz8xdz1Wn8DGjfA',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
MATCH (x:IMKLTelecomCable)
WITH x, [
//    {property: 'grp:currentStatus', value: x.`grp:currentStatus`, mandatory: true, enum: ['functional', 'projected', 'disused']},
//    {property: 'grp:inNetwork', value: x.`grp:inNetwork`, mandatory: true, enum: ['electricity', 'telecommunications', 'crossTheme']},
    {property: 'grp:kleur', value: x.`grp:kleur`, maxLength: 256},
    {property: 'grp:subThema', value: x.`grp:subThema`, mandatory: true, enum: ['elektronischeCommunicatie']},
    {property: 'grp:telecommunicationsCableMaterialType', value: x.`grp:telecommunicationsCableMaterialType`, mandatory: true, enum: [
    'andere', 'eo-ymekaszh', 'fo-so', 'f-utp', 'f-utp-cat5', 'f-utp-cat-5', 'f-utp-cat5e', 'f-utp-cat-5e', 'f-utp-cat5e-outdoor', 'f-utp-cat-5e-outdoor', 
    'f-utp-cat5-outdoor', 'f-utp-cat-5-outdoor', 'f-utp-cat6', 'f-utp-cat-6', 'f-utp-cat6outdoor', 'f-utp-cat6-outdoor', 'je-h(st)h-rf-1h', 'j-h(st)h-bd', 
    'rg11', 'rg12', 'rg59', 'rg6', 'stralende-kabel', 'tpgf', 'twavb', 'utp', 'utp-cat5', 'utp-cat5e', 'utp-cat5e-outdoor', 'utp-cat6', 'utp-cat6outdoor', 
    'utp-cat6-outdoor', 'u-utp-cat-5e', 'u-utp-cat-6e', 'u-utp-cat-6e-outdoor', 'u-utp-categorie-5e-outdoor', 'uxl', 'coax', 'coax-rg11', 'coax-rg12', 
    'coax-rg59', 'cu', 'elec', 'gefaradiseerde-kabel', 'koperkabel', 'li2ycy', 'liy(st)yy', 'liycy', 'liycy(tp)', 'profibuskabel', 'svab', 'svavb', 
    'svavb-f2', 'svv-f2', 'sxag-f2', 'sxavb', 'xlpe', 'alupet', 'alu-pet', 'app', 'appj', 'app-pe', 'f.o.', 'glasvezel', 'mok', 'mok-micro', 'muk', 
    'onbekend', 'pepy', 'rg6a', 'rtt-34', 'teletransmissiekabel-uit-kwarten', 'other', 'twistedpair', 'coaxial', 'opticalfiber', 'tvavb', 'sty-sy',
     'ftp', 'vvt'
    ]},
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
