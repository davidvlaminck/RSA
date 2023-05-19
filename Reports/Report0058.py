from DQReport import DQReport


class Report0058:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0058',
                               title='Er zijn geen assets die het doel zijn van twee of meer Voedt relaties.',
                               spreadsheet_id='15knbCKB7xWKDX_7utnDBsNe2mYHxGwM6cl8bPwg6q5k',
                               datasource='Neo4J',
                               persistent_column='H')

        self.report.result_query = """
            MATCH (a {isActief: TRUE})<-[:Voedt]-(v {isActief: TRUE})
            WHERE NOT (v:onderdeel) AND NOT (v:UPSLegacy)
            WITH a, count(v) as v_count 
            WHERE v_count > 1 
            RETURN 
                DISTINCT a.uuid as uuid, a.naampad as naampad, a.toestand as toestand, 
                a.`tz:toezichter.tz:voornaam` as tz_voornaam, a.`tz:toezichter.tz:naam` as tz_naam, a.`tz:toezichter.tz:email` as tz_email,
                a.`tz:toezichtgroep.tz:naam` as tzg_naam,  a.`tz:toezichtgroep.tz:referentie` as tzg_referentie
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# sparql query:

# PREFIX inst: <https://lgc.data.wegenenverkeer.be/ns/installatie#>
# PREFIX imel: <https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#>
# PREFIX ond: <https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# PREFIX toezicht: <https://wegenenverkeer.data.vlaanderen.be/oef/toezicht/>
#
# select ?doel ?naampad ?toestand ?toezichter_voornaam ?toezichter_naam ?toezichter_email ?toezichtgroep_naam ?toezichtgroep_ref where {
#     ?doel imel:NaampadObject.naampad ?naampad ;
#         imel:AIMToestand.toestand ?toestand .
#     OPTIONAL {
#         ?doel toezicht:Toezicht.toezichter ?toezichter .
#         ?toezichter toezicht:DtcToezichter.voornaam ?toezichter_voornaam ;
#             toezicht:DtcToezichter.naam ?toezichter_naam ;
#             toezicht:DtcToezichter.email ?toezichter_email } .
#     OPTIONAL {
#         ?doel toezicht:Toezicht.toezichtgroep ?toezichtgroep .
#         ?toezichtgroep toezicht:DtcToezichtGroep.naam ?toezichtgroep_naam ;
#         	toezicht:DtcToezichtGroep.referentie ?toezichtgroep_ref } .
#     {
#         select ?doel where {
#             ?bron imel:AIMDBStatus.isActief "true"^^xsd:boolean .
#             ?doel imel:AIMDBStatus.isActief "true"^^xsd:boolean .
#             ?voedt a ond:Voedt .
#             ?voedt imel:RelatieObject.doel ?doel .
#             ?voedt imel:RelatieObject.bron ?bron .
#             FILTER (NOT EXISTS {?bron a inst:UPSLegacy})
#         }
#         GROUP BY ?doel ?naampad ?toestand
#         HAVING(COUNT(?voedt) > 1)
#         order by ?doel
# 	}
# }