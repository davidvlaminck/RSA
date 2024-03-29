from DQReport import DQReport


class Report0054:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0054',
                               title='Akela IMKL constraints for Manhole',
                               spreadsheet_id='19xHbOaA3wWBujILYCy2UgYfkD_fu1DI0YmodWqm2HBc',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            MATCH (x:IMKLManhole) // currentStatus mandatory
            WHERE x.`grp:currentStatus` IS NULL
            RETURN x.uuid as uuid, 'currentStatus' as property, 'is null/empty but mandatory' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLManhole) // currentStatus enumeration
            WHERE x.`grp:currentStatus` IS NOT NULL AND NOT x.`grp:currentStatus` IN ['functional','projected','disused']
            RETURN x.uuid as uuid, 'currentStatus' as property, 'value not in enumeration' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLManhole) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLManhole) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLManhole) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLManhole) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 255
            RETURN x.uuid as uuid, 'uuid' as property, 'max length is 255' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
