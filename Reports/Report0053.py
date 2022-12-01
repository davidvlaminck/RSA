from DQReport import DQReport


class Report0053:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0053',
                               title='Akela IMKL constraints for ExtraPlan',
                               spreadsheet_id='1gyq2c-qJIHzOpENLb0KF6zlbTLg-dAjsSyUNSh8wkc0',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            MATCH (x:IMKLExtraPlan) // extraPlanType mandatory
            WHERE x.`grp:extraPlantype` IS NULL
            RETURN x.uuid as uuid, 'extraPlanType' as property, 'is null/empty but mandatory' as fault, x.`grp:extraPlantype` as property_value
            UNION
            MATCH (x:IMKLExtraPlan) // extraPlanType enumeration
            WHERE x.`grp:extraPlantype` IS NOT NULL AND NOT x.`grp:extraPlantype` IN ['detailplan','lengteprofiel','gestuurdeBoring','andere','veiligheidsVoorschriften']
            RETURN x.uuid as uuid, 'extraPlanType' as property, 'value not in enumeration' as fault, x.`grp:extraPlantype` as property_value
            UNION
            MATCH (x:IMKLExtraPlan) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLExtraPlan) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLExtraPlan) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLExtraPlan) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 255
            RETURN x.uuid as uuid, 'uuid' as property, 'max length is 255' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
