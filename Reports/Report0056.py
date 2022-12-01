from DQReport import DQReport


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
            MATCH (x:IMKLTelecomCable) // currentStatus mandatory
            WHERE x.`grp:currentStatus` IS NULL
            RETURN x.uuid as uuid, 'currentStatus' as property, 'is null/empty but mandatory' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // currentStatus enumeration
            WHERE x.`grp:currentStatus` IS NOT NULL AND NOT x.`grp:currentStatus` IN ['functional','projected','disused']
            RETURN x.uuid as uuid, 'currentStatus' as property, 'value not in enumeration' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // kleur max length
            WHERE x.`grp:kleur` IS NOT NULL AND size(x.`grp:kleur`) > 256
            RETURN x.uuid as uuid, 'kleur' as property, 'max length is 256' as fault, x.`grp:kleur` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // subThema mandatory
            WHERE x.`grp:subThema` IS NULL
            RETURN x.uuid as uuid, 'subThema' as property, 'is null/empty but mandatory' as fault, x.`grp:subThema` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // subThema enumeration
            WHERE x.`grp:subThema` IS NOT NULL AND NOT x.`grp:subThema` IN ['elektronischeCommunicatie']
            RETURN x.uuid as uuid, 'subThema' as property, 'value not in enumeration' as fault, x.`grp:subThema` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // telecommunicationsCableMaterialType mandatory
            WHERE x.`grp:telecommunicationsCableMaterialType` IS NULL
            RETURN x.uuid as uuid, 'telecommunicationsCableMaterialType' as property, 'is null/empty but mandatory' as fault, x.`grp:telecommunicationsCableMaterialType` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // telecommunicationsCableMaterialType enumeration
            WHERE x.`grp:telecommunicationsCableMaterialType` IS NOT NULL AND NOT x.`grp:telecommunicationsCableMaterialType` IN ['coaxial','opticalFiber','twistedPair','other']
            RETURN x.uuid as uuid, 'telecommunicationsCableMaterialType' as property, 'value not in enumeration' as fault, x.`grp:telecommunicationsCableMaterialType` as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLTelecomCable) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 255
            RETURN x.uuid as uuid, 'uuid' as property, 'max length is 255' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
