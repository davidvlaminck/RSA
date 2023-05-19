from DQReport import DQReport


class Report0040:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0040',
                               title='DNBLaagspanning/DNBHoogspanning hebben een HoortBij relatie naar LS/HS respectievelijk',
                               spreadsheet_id='1WLXykE5pX9wiBqnSgJ1HTE8dtkjRydMxAnccLV3T1_U',
                               datasource='Neo4J',
                               persistent_column='D')

        self.report.result_query = """MATCH (dnbl:DNBLaagspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbl)-[:HoortBij]->(:LS {isActief: TRUE}))
            RETURN dnbl.uuid as uuid, dnbl.naam as naam, dnbl.typeURI as typeURI
            UNION
            MATCH (dnbh:DNBHoogspanning {isActief: TRUE})
            WHERE NOT EXISTS((dnbh)-[:HoortBij]->(:HS {isActief: TRUE}))
            RETURN dnbh.uuid as uuid, dnbh.naam as naam, dnbh.typeURI as typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

# SPARQL query
# PREFIX inst: <https://lgc.data.wegenenverkeer.be/ns/installatie#>
# PREFIX imel: <https://wegenenverkeer.data.vlaanderen.be/ns/implementatieelement#>
# PREFIX ond: <https://wegenenverkeer.data.vlaanderen.be/ns/onderdeel#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
#
# SELECT ?asset ?naam ?type
# WHERE {
#     {
#         ?asset a ond:DNBLaagspanning ;
#             imel:AIMDBStatus.isActief "true"^^xsd:boolean ;
#             imel:AIMNaamObject.naam ?naam ;
#             a ?type .
#         FILTER(NOT EXISTS{
#             ?hoortbij a ond:HoortBij .
#             ?hoortbij imel:RelatieObject.doel ?legacy .
#             ?hoortbij imel:RelatieObject.bron ?asset .
#             ?legacy a inst:LS  })
#     } UNION {
#         ?asset a ond:DNBHoogspanning ;
#             imel:AIMDBStatus.isActief "true"^^xsd:boolean ;
#             imel:AIMNaamObject.naam ?naam ;
#             a ?type .
#         FILTER(NOT EXISTS{
#             ?hoortbij a ond:HoortBij .
#             ?hoortbij imel:RelatieObject.doel ?legacy .
#             ?hoortbij imel:RelatieObject.bron ?asset .
#             ?legacy a inst:HS  })
#     }
# }
