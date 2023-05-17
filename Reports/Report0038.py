from DQReport import DQReport


class Report0038:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0038',
                               title="IP AS1 elementen hebben een .ODF TT tegenhanger",
                               spreadsheet_id='1rDCUE7kj0ZcCVtFe2EiIqKMz7fdR5J6mtpU6lRpzpbI',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (i:IP {isActief:TRUE})
        WHERE i.naam contains '.AS1'
        WITH i, split(i.naampad,'/') AS splitted
        WITH i, apoc.text.join(reverse(tail(reverse(splitted))),'/') + '/' AS naampad_beh
        OPTIONAL MATCH (t:TT {isActief:TRUE})
        WHERE t.naampad contains naampad_beh AND t.naam contains 'ODF'
        WITH i, t
        WHERE t.uuid IS NULL
        RETURN i.uuid, i.naampad, i.`tz:toezichter.tz:gebruikersnaam` AS toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# sparql equivalent:
# PREFIX geo: <http://www.opengis.net/ont/geosparql#>
# PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
# PREFIX inst: <https://lgc.data.wegenenverkeer.be/ns/installatie#>
# PREFIX imel: <https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#>
# PREFIX ond: <https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#>
# PREFIX abs: <https://wegenenverkeer.data.vlaanderen.be/ns/abstracten#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# PREFIX toezicht: <https://wegenenverkeer.data.vlaanderen.be/oef/toezicht/>
#
# SELECT ?ip ?ip_naampad ?toezichter_naam ?tt ?tt_naampad
# WHERE {
#     ?ip a inst:IP ;
#         imel:NaampadObject.naampad ?ip_naampad ;
#         imel:AIMDBStatus.isActief "true"^^xsd:boolean ;
#         toezicht:Toezicht.toezichter ?toezichter .
#     ?toezichter toezicht:DtcToezichter.gebruikersnaam ?toezichter_naam
#     BIND (STRBEFORE(?ip_naampad, "/") AS ?beh).
#     FILTER (STRENDS(?ip_naampad, ".AS1" )).
#     FILTER (NOT EXISTS {?tt a inst:TT .
#         ?tt imel:AIMDBStatus.isActief "true"^^xsd:boolean ;
#             imel:NaampadObject.naampad ?tt_naampad .
#         FILTER (STRENDS(?tt_naampad, ".ODF" ) &&
#             STRSTARTS(?tt_naampad, ?beh) )
# 	})
# }