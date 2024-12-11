from DQReport import DQReport


class Report0106:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0106', title='Geometrie is consistent met GeometrieArtefact',
                               spreadsheet_id='1x9g0b_wQtLgkxnAwR_lffzVLdS3PElb3mLWtqItqkig', datasource='PostGIS',
                               persistent_column='K')

        self.report.result_query = """
            with cte_geometry_artefact(uri,label_nl,geen_geometrie,punt3D,lijn3D,polygoon3D,gewijzigd_sinds) as (
                  VALUES
                    ('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Baanlichaam', 'Baanlichaam', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#BlindePut', 'Blinde put', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Ecoduct', 'Ecoduct', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Ecoduiker', 'Ecoduiker', '0', '0', '1', '1', 'GA_2.12.0')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Ecokoker', 'Ecokoker', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Ecotunnel', 'Ecotunnel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Ecovallei', 'Ecovallei', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Fietstelinstallatie', 'Fietstelinstallatie', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Gebouw', 'Gebouw', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#GecombineerdePut', 'Gecombineerde put', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#GeluidwerendeConstructie', 'Geluidwerende constructie', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#GroepDwarseMarkeringEnFiguratie', 'Groep dwarse- en figuratiemarkering', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#GroepMarkering', 'Groepering alle soorten markering', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Gronddam', 'Gronddam', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Hulppost', 'Hulppost', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#InspectieputRiolering', 'Inspectieput riolering', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#IPBackbone', 'IP backbone', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#L2AccessStructuur', 'L2 access structuur', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Link', 'Link', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Lokaal', 'Lokaal', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Luchtkwaliteitsensor', 'Luchtkwaliteitsensor', '0', '1', '0', '0', 'GA_2.11.0')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#MIVInstallatie', 'MIV-installatie', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Onderbord', 'Onderbord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Pad', 'Pad', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Rioleringsstelsel', 'Rioleringsstelsel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Slagboom', 'Slagboom installatie', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Trajectcontrole', 'Trajectcontrole', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#VerkeersbordConcept', 'Verkeersbordconcept', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Verkeersbordopstelling', 'Verkeersbordopstelling', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#VerkeersbordVerkeersteken', 'Verkeersbord - verkeersteken', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#VLAN', 'VLAN', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Wegberm', 'Wegberm', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/installatie#Zpad', 'Zpad', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Aansluitmof', 'Aansluitmof', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Aansluitopening', 'Aansluitopening', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Aanstraalverlichting', 'Aanstraalverlichting', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Afmetingsensor', 'Afmetingsensor', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Afscherming', 'Afscherming', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Afsluiter', 'Afsluiter', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Aftakking', 'Aftakking', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AIDModule', 'AID-module', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AnalogeHoppinzuil', 'Analoge hoppinzuil', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ANPRCamera', 'ANPR camera', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Antenne', 'Antenne', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#AntiParkeerpaal', 'Antiparkeerpaal', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Armatuurcontroller', 'Armatuurcontroller', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Audioversterker', 'Audioversterker', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Batterij', 'Batterij', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bel', 'Bel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BeschermingWapening', 'Bescherming wapening', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanBetonstraatsteen', 'Bestrating van betonstraatsteen', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanBetontegel', 'Bestrating van betontegel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanGebakkenStraatsteen', 'Bestrating van gebakken straatsteen', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanGrasbetontegel', 'Bestrating van grasbetontegel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanKassei', 'Bestrating van kassei', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanMozaiekkei', 'Bestrating van mozaiekkei', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BestratingVanNatuursteentegel', 'Bestrating van natuursteentegel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bestrijking', 'Bestrijking', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bevestigingsbeugel', 'Bevestigingsbeugel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BijzonderGeluidsschermelement', 'BijzonderGeluidsschermelement', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Binnenverlichtingstoestel', 'Binnenverlichtingstoestel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BitumineuzeLaag', 'Bitumineuze laag', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BloemrijkGlanshavergrasland', 'Bloemrijk glanshavergrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BloemrijkGraslandGraslandfase4', 'Bloemrijk grasland - fase4', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BloemrijkStruisgrasgrasland', 'Bloemrijk struisgrasgrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BloemrijkVochtigTotNatGrasland', 'Bloemrijk vochtig tot nat grasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BoogpaalVerkeerslicht', 'Boogpaal verkeerslicht', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Boom', 'Boom', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Boombrug', 'Boombrug', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bouwput', 'Bouwput', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Bovenbouw', 'Bovenbouw', '0', '1', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Braam', 'Braam', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Brandblusser', 'Brandblusser', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Brandhaspel', 'Brandhaspel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Brandleiding', 'Brandleiding', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Brandnetelruigte', 'Brandnetelruigte', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#BremEnGaspeldoornstruweel', 'Brem en gaspeldoornstruweel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Buisbekleding', 'Buisbekleding', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Cabine', 'Cabine', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Cabinecontroller', 'Cabinecontroller', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Calamiteitendoorsteek', 'Calamiteitendoorsteek', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#CalamiteitsBord', 'Calamiteitsbord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Camera', 'Camera', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Cementbetonverharding', 'Cementbetonverharding', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Cluster', 'Cluster', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Codeklavier', 'Codeklavier', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ColloidaalBeton', 'Colloidaal beton', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Combilantaarn', 'Combilantaarn', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ConstructieSokkel', 'Constructie sokkel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Contactor', 'Contactor', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Contactpunt', 'Contactpunt', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Container', 'Container', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Contourverlichting', 'Contourverlichting', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Damwand', 'Damwand', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DetectieCamera', 'Detectie camera', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Dieselgenerator', 'Dieselgenerator', '0', '1', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Dilatatie', 'Dilatatie', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Divergentiepuntbebakeningselement', 'Divergentiepuntbebakeningselement', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DNBHoogspanning', 'DNB hoogspanning', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DNBLaagspanning', 'DNB laagspanning', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Dolomietverharding', 'Dolomietverharding', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DominantGraslandfase2', 'Dominant grasland - fase2', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Dongle', 'Dongle', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Doorgang', 'Doorgang', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Doornstruweel', 'Doornstruweel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Draineerbuis', 'Draineerbuis', '0', '1', '1', '0', 'GA_2.8.0')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Drukknop', 'Drukknop', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Drukverhogingsgroep', 'Drukverhogingsgroep', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Duikschot', 'Duikschot', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Duingrasland', 'Duingrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DunneOverlaging', 'Dunne overlaging', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DwarseMarkering', 'Dwarse markering', '0', '0', '1', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DwarseMarkeringVerschuind', 'Dwarse markering verschuind', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Dwerghavergrasland', 'Dwerghavergrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DwergstruikvegetatieHeidesoorten', 'Dwergstruikvegetatie heidesoorten', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynamischeVluchtwegindicatie', 'Dynamische vluchtwegindicatie', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordExternePU', 'Processing unit voor dynamisch borden', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordOpMaat', 'Dynamisch bord op maat', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordPK', 'Pijl-Kruis-bord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordRSS', 'RSS-bord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordRVMS', 'RVMS-bord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordVMS', 'VMS-bord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#DynBordZ30', 'Dynamisch Zone-30 bord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EcoPoort', 'Eco poort', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Ecoraster', 'Ecoraster', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Eindstuk', 'Eindstuk', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EnergiemeterAWV', 'Energiemeter AWV', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EnergiemeterDerden', 'Energiemeter derden', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EnergiemeterDNB', 'Energiemeter DNB', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EnergiemeterDNBPiek', 'Energiemeter DNB piek', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#EnergiemeterDNBReactief', 'Energiemeter DNB reactief', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Exoten', 'Exoten', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ExterneDetectie', 'Externe detectie', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#FieldOfView', 'Field-of-View', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Fietslantaarn', 'Fietslantaarn', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#FietstelDisplay', 'Fietstel display', '0', '1', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Fietstelsysteem', 'Fietstelsysteem', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#FiguratieMarkering', 'Figuratiemarkering', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#FiguratieMarkeringVerschuind', 'Figuratie markering verschuind', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ForfaitaireAansluiting', 'Forfaitaire aansluiting', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Funderingsmassief', 'Funderingsmassief', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Funderingsplaat', 'Funderingsplaat', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Galgpaal', 'Galgpaal', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GeexpandeerdPolystyreen', 'Geexpandeerd polystyreen', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GekleurdWegvlakMarkering', 'Gekleurd wegvlak markering', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geleideconstructie', 'Geleideconstructie', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geleidingsverlichting', 'Geleidingsverlichting', '0', '1', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geleidingswand', 'Geleidingswand', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GeluidswerendeConstructie', 'Geluidswerende constructie', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Geotextiel', 'Geotextiel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GetesteBeginconstructie', 'Geteste beginconstructie', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GPU', 'GPU', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GrasKruidenmixGraslandfase3', 'Gras kruidenmix grasland - fase3', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Grasland', 'Grasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Grasmat', 'Grasmat', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#GrassenmixGraslandfase1', 'Grassenmix grasland - fase1', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Grindgazon', 'Grindgazon', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Haag', 'Haag', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Handbediening', 'Handbediening', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Handwiel', 'Handwiel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hardware', 'Hardware', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Heestermassief', 'Heestermassief', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#HeischraalGrasland', 'Heischraal grasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hoofdschakelaar', 'Hoofdschakelaar', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hoogtedetectie', 'Hoogtedetectie', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#HSBeveiligingscel', 'HS beveiligingscel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#HSCabine', 'HS-cabine', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Huisaansluitput', 'Huisaansluitput', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hulppostkast', 'Hulppostkast', '0', '1', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hulpstuk', 'Hulpstuk', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Hydrant', 'Hydrant', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Iepenstruweel', 'Iepenstruweel', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#IndoorKast', 'Indoor kast', '0', '1', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Infiltratievoorziening', 'Infiltratievoorziening', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#IntercomServer', 'Intercom server', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#IntercomToestel', 'Intercom toestel', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#InvasieveExoten', 'Invasieve exoten', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#InwendigVerlichtPictogram', 'Inwendig verlicht pictogram', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#IOKaart', 'IO-Kaart', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#IpPowerSwitch', 'IP powerswitch', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#ITSapp', 'ITSapp', '1', '0', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Kabelmof', 'Kabelmof', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KabelnetToegang', 'Kabelnet toegang', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Kalkgrasland', 'Kalkgrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KalkrijkKamgrasland', 'Kalkrijk kamgrasland', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Kamer', 'Kamer', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KantstrookAfw', 'Afwijkende kantstrook', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KantstrookStd', 'Gestandaardiseerde Kantstrook', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Klimatisatie', 'Klimatisatie', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Klimvorm', 'Klimvorm', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Knipperlantaarn', 'Knipperlantaarn', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Kopmuur', 'Kopmuur', '0', '0', '0', '1', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#KringsBerliner', 'Krings Berliner', '0', '0', '1', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Laagspanningsbord', 'Laagspanningsbord', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LEDDriver', 'LED-driver', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LetterCijferMarkering', 'Letter-cijfer markering', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LetterMarkeringVerschaald', 'Verschaalde letter markering', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Lichtmast', 'Lichtmast', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#Lichtsensor', 'Lichtsensor', '0', '1', '0', '0', '')
                    ,('https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#LijnvormigElementMarkering', 'Lijnvormig element markering', '0', '0', '1', '0', '')
                ), cte_asset_withGeomInfo as (
                    select
                        a.uuid
                        , a.actief
                        , a.toestand
                        , at.uuid as assettype_uuid
                        , at.naam
                        , at.uri
                        , coalesce(g.wkt_string, l.geometrie) as wkt_string
                        , g.geo_niveau
                        -- Extract the asset geometry type from the wkt_string (OTL or Legacy)
                        , case
                            when
                                coalesce(g.wkt_string, l.geometrie) is null then 1
                                else 0
                        end as geen_geometrie
                        , case
                            when
                                SUBSTRING(coalesce(g.wkt_string, l.geometrie) FROM '(POINT Z|LINESTRING Z|POLYGON Z)') = 'POINT Z'
                            then 1
                            else 0
                        end as punt3D
                        , case
                            when
                                SUBSTRING(coalesce(g.wkt_string, l.geometrie) FROM '(POINT Z|LINESTRING Z|POLYGON Z)') = 'LINESTRING Z'
                            then 1
                            else 0
                        end as lijn3D
                        , case
                            when
                                SUBSTRING(coalesce(g.wkt_string, l.geometrie) FROM '(POINT Z|LINESTRING Z|POLYGON Z)') = 'POLYGON Z'
                            then 1
                            else 0
                        end as polygoon3D
                    from assets a 
                    left join geometrie g on a.uuid = g.assetuuid
                    left join locatie l on a.uuid = l.assetuuid
                    left join assettypes at on a.assettype = at.uuid
                    where
                        a.actief = true
                )
            -- Main query
            select
                a.uuid
                , a.naam
                , LEFT(a.wkt_string, 50) as wkt_string
                , a.geo_niveau as level_of_geometrie
                , a.actief
                , a.toestand
                , ga.uri
                -- Het actuele geometrie type
                ,
                case
                    WHEN a.geen_geometrie = '1' THEN 'geen_geometrie'
                    ELSE ''
                END ||
                case
                    WHEN a.punt3D = '1' THEN 'punt3D'
                    ELSE ''
                END ||
                CASE
                    WHEN a.lijn3D = '1' THEN 'lijn3D'
                    ELSE ''
                END ||
                CASE
                    WHEN a.polygoon3D = '1' THEN 'polygoon3D'
                    ELSE ''
                END AS OTL_actuele_geometrie
                -- Het verwachte geometrie type
                ,
                case
                    WHEN ga.geen_geometrie = '1' THEN 'geen_geometrie '
                    ELSE ''
                END ||
                case
                    WHEN ga.punt3D = '1' THEN 'punt3D '
                    ELSE ''
                END ||
                CASE
                    WHEN ga.lijn3D = '1' THEN 'lijn3D '
                    ELSE ''
                END ||
                CASE
                    WHEN ga.polygoon3D = '1' THEN 'polygoon3D '
                    ELSE ''
                END AS GA_verwachte_geometrie
                , 'GA_2.13.0' as GA_Versie
            from cte_asset_withGeomInfo a -- a staat voor assets
            left join cte_geometry_artefact ga on a.uri = ga.uri -- ga staat voor GeometrieArtefact
            where
                ga.uri is not null -- om o.a. de groeperingen uit de resultaten te filteren
                AND
                a.actief IS true
                and
                -- Een asset heeft 1 bepaalde geometrie, stemt dit overeen met het verwachte GA?
                (
                a.geen_geometrie = 1 and a.geen_geometrie != ga.geen_geometrie::int
                or
                a.punt3D = 1 and a.punt3D != ga.punt3D::int
                or
                a.lijn3D = 1 and a.lijn3D != ga.lijn3D::int
                or
                a.polygoon3D = 1 and a.polygoon3D != ga.polygoon3D::int
                )
            order by naam, otl_actuele_geometrie, toestand
	"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
