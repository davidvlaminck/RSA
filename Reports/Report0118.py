from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0118(BaseReport):
    def init_report(self) -> None:
        aql_query = """
FOR at IN assettypes
  FILTER CONTAINS(at.short_uri, "installatie")
  FOR a IN assets
    FILTER a.assettype_key == at._key
    FILTER a.AIMDBStatus_isActief == true
    FOR b IN bestekkoppelingen
      FILTER b._from == a._id
      FILTER b.bestekuuid == null
      RETURN DISTINCT {
        uuid: a._key,
        typeURI: at.short_uri,
        naampad: a.AIMNaamObject_naampad,
        naam: a.AIMNaamObject_naam
      }
        """
        self.report = DQReport(name='report0118',
                               title='Elke installatie heeft een bestekkoppeling',
                               spreadsheet_id='1bpZLWgqFp6AsRqxaTCnvc8IqpnnmSnoajlCABGD4TbY',
                               datasource='ArangoDB',
                               persistent_column='E',
                               excel_filename='[RSA] Elke installatie heeft een bestekkoppeling.xlsx',)

        self.report.result_query = aql_query

        self.report.cypher_query = """
            MATCH (a:Asset {isActief: TRUE})-[:HeeftBestek]->(b:Bestek)
            WHERE b.bestekuuid IS NULL
            RETURN DISTINCT a.uuid AS uuid, a.typeURI AS typeURI, a.naampad AS naampad, a.naam AS naam
        """

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)