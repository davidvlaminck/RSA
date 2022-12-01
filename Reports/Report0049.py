from DQReport import DQReport


class Report0049:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0049',
                               title='Akela IMKL constraints for ActivityComplex',
                               spreadsheet_id='1O3nyZRjhY3RT4hK39eHxfT6zY4QgBZ-qfth7ywKq0_o',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            MATCH (x:IMKLActivityComplex) // activity mandatory
            WHERE x.`grp:activity` IS NULL
            RETURN x.uuid as uuid, 'activity' as property, 'is null/empty but mandatory' as fault, x.`grp:activity` as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // activity max length
            WHERE x.`grp:activity` IS NOT NULL AND size(x.`grp:activity`) > 20
            RETURN x.uuid as uuid, 'activity' as property, 'max length is 20' as fault, x.`grp:activity` as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // name max length
            WHERE x.`grp:name` IS NOT NULL AND size(x.`grp:name`) > 200
            RETURN x.uuid as uuid, 'name' as property, 'max length is 200' as fault, x.`grp:name` as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLActivityComplex) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 50
            RETURN x.uuid as uuid, 'activity' as property, 'max length is 50' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
