from DQReport import DQReport


class Report0049:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0049',
                               title='Akela IMKL constraints for ActivityComplex',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            MATCH (ac:IMKLActivityComplex) // activity mandatory
            WHERE ac.`grp:activity` IS NULL
            RETURN ac.uuid as uuid, 'activity' as property, 'is null/empty but mandatory' as fault, ac.`grp:activity` as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // activity max length
            WHERE ac.`grp:activity` IS NOT NULL AND size(ac.`grp:activity`) > 20
            RETURN ac.uuid as uuid, 'activity' as property, 'max length is 20' as fault, ac.`grp:activity` as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // inNetwork mandatory
            WHERE ac.`grp:inNetwork` IS NULL
            RETURN ac.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, ac.`grp:inNetwork` as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // inNetwork enumeration
            WHERE ac.`grp:inNetwork` IS NOT NULL AND NOT ac.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN ac.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, ac.`grp:inNetwork` as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // name max length
            WHERE ac.`grp:name` IS NOT NULL AND size(ac.`grp:name`) > 200
            RETURN ac.uuid as uuid, 'name' as property, 'max length is 200' as fault, ac.`grp:name` as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // uuid mandatory
            WHERE ac.uuid IS NULL
            RETURN ac.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, ac.uuid as property_value
            UNION
            MATCH (ac:IMKLActivityComplex) // uuid max length
            WHERE ac.uuid IS NOT NULL AND size(ac.uuid) > 50
            RETURN ac.uuid as uuid, 'activity' as property, 'max length is 50' as fault, ac.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
