from DQReport import DQReport


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
            MATCH (x:IMKLPipe) // containerType mandatory
            WHERE x.`grp:containerType` IS NULL
            RETURN x.uuid as uuid, 'containerType' as property, 'is null/empty but mandatory' as fault, x.`grp:containerType` as property_value
            UNION
            MATCH (x:IMKLPipe) // containerType enumeration
            WHERE x.`grp:containerType` IS NOT NULL AND NOT x.`grp:containerType` IN ['mantelbuis', 'kabelEnLeidingGoot']
            RETURN x.uuid as uuid, 'containerType' as property, 'value not in enumeration' as fault, x.`grp:containerType` as property_value
            UNION
            MATCH (x:IMKLPipe) // currentStatus mandatory
            WHERE x.`grp:currentStatus` IS NULL
            RETURN x.uuid as uuid, 'currentStatus' as property, 'is null/empty but mandatory' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLPipe) // currentStatus enumeration
            WHERE x.`grp:currentStatus` IS NOT NULL AND NOT x.`grp:currentStatus` IN ['functional','projected','disused']
            RETURN x.uuid as uuid, 'currentStatus' as property, 'value not in enumeration' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLPipe) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLPipe) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLPipe) // kleur max length
            WHERE x.`grp:kleur` IS NOT NULL AND size(x.`grp:kleur`) > 256
            RETURN x.uuid as uuid, 'kleur' as property, 'max length is 256' as fault, x.`grp:kleur` as property_value
            UNION
            MATCH (x:IMKLPipe) // pipeDiameter mandatory
            WHERE x.`grp:pipeDiameter` IS NULL
            RETURN x.uuid as uuid, 'pipeDiameter' as property, 'is null/empty but mandatory' as fault, x.`grp:pipeDiameter` as property_value
            UNION
            MATCH (x:IMKLPipe) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLPipe) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 255
            RETURN x.uuid as uuid, 'uuid' as property, 'max length is 255' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
