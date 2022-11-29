from DQReport import DQReport


class Report0052:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0052',
                               title='Akela IMKL constraints for ElectricityCable',
                               spreadsheet_id='',
                               datasource='Neo4J',
                               persistent_column='E')

        self.report.result_query = """
            MATCH (x:IMKLElectricityCable) // currentStatus mandatory
            WHERE x.`grp:currentStatus` IS NULL
            RETURN x.uuid as uuid, 'currentStatus' as property, 'is null/empty but mandatory' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // currentStatus enumeration
            WHERE x.`grp:currentStatus` IS NOT NULL AND NOT x.`grp:currentStatus` IN ['functional','projected','disused']
            RETURN x.uuid as uuid, 'currentStatus' as property, 'value not in enumeration' as fault, x.`grp:currentStatus` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // inNetwork mandatory
            WHERE x.`grp:inNetwork` IS NULL
            RETURN x.uuid as uuid, 'inNetwork' as property, 'is null/empty but mandatory' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // inNetwork enumeration
            WHERE x.`grp:inNetwork` IS NOT NULL AND NOT x.`grp:inNetwork` IN ['electricity','telecommunications','crossTheme']
            RETURN x.uuid as uuid, 'inNetwork' as property, 'value not in enumeration' as fault, x.`grp:inNetwork` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // kleur max length
            WHERE x.`grp:kleur` IS NOT NULL AND size(x.`grp:kleur`) > 256
            RETURN x.uuid as uuid, 'kleur' as property, 'max length is 256' as fault, x.`grp:kleur` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // nominalVoltage mandatory
            WHERE x.`grp:nominalVoltage` IS NULL
            RETURN x.uuid as uuid, 'nominalVoltage' as property, 'is null/empty but mandatory' as fault, x.`grp:nominalVoltage` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // operatingVoltage mandatory
            WHERE x.`grp:operatingVoltage` IS NULL
            RETURN x.uuid as uuid, 'operatingVoltage' as property, 'is null/empty but mandatory' as fault, x.`grp:operatingVoltage` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // subThema mandatory
            WHERE x.`grp:subThema` IS NULL
            RETURN x.uuid as uuid, 'subThema' as property, 'is null/empty but mandatory' as fault, x.`grp:subThema` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // subThema enumeration
            WHERE x.`grp:subThema` IS NOT NULL AND NOT x.`grp:subThema` IN ['elektriciteitTransport','elektriciteitTransportPlaatselijk','elektriciteitDistributieHoogspanning','elektriciteitDistributieLaagspanning','elektriciteitOpenbareVerlichting','elektriciteitVerkeerslichten','elektriciteitVerkeershandhavingssystemen']
            RETURN x.uuid as uuid, 'subThema' as property, 'value not in enumeration' as fault, x.`grp:subThema` as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // uuid mandatory
            WHERE x.uuid IS NULL
            RETURN x.uuid as uuid, 'uuid' as property, 'is null/empty but mandatory' as fault, x.uuid as property_value
            UNION
            MATCH (x:IMKLElectricityCable) // uuid max length
            WHERE x.uuid IS NOT NULL AND size(x.uuid) > 255
            RETURN x.uuid as uuid, 'uuid' as property, 'max length is 255' as fault, x.uuid as property_value
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
