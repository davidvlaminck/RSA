from lib.reports.DQReport import DQReport
from lib.reports.BaseReport import BaseReport


class Report0102(BaseReport):
    def init_report(self) -> None:
        aql_query = """
        FOR imkl IN assets
          FILTER imkl.assettype_key == "b62ac453"
          FILTER imkl.AIMDBStatus_isActief == true

          /* DeelVan relation: otl -> imkl */
          FOR dv IN assetrelaties
            FILTER dv._to == imkl._id
            FILTER dv.relatietype_key == "afbe"
            LET otl = DOCUMENT(dv._from)
            FILTER otl != null AND otl.AIMDBStatus_isActief == true

            /* Get OTL assettype URI */
            LET otl_type = DOCUMENT(CONCAT("assettypes/", otl.assettype_key))

            /* HoortBij relation: otl -> legacy */
            LET hb = FIRST(
              FOR e IN assetrelaties
                FILTER e._from == otl._id
                FILTER e.relatietype_key == "812d"
                LET legacy = DOCUMENT(e._to)
                FILTER legacy != null AND legacy.AIMDBStatus_isActief == true
                RETURN legacy
            )

            /* Exclude if legacy is RIOOL */
            FILTER hb == null OR hb.assettype_key != "37b4af66"

            /* Check for toezichtgroep */
            LET has_toezichtsgroep = FIRST(
              FOR b IN betrokkenerelaties
                FILTER b._from == otl._id
                FILTER b.rol == "toezichtsgroep"
                RETURN b
            )

            FILTER has_toezichtsgroep == null

            RETURN {
              uuid: otl._key,
              uri: otl_type.uri
            }
        """

        self.report = DQReport(name='report0102',
                               title='IMKLActivityComplex afgeleiden zonder toezichtgroep',
                               spreadsheet_id='1fbnP-heDtQnG9Q5kF1DA_cn3cY7egNFRgXMB4QaZKZk',
                               datasource='ArangoDB',
                               persistent_column='C',
                               excel_filename='[RSA] IMKLActivityComplex afgeleiden zonder toezichtgroep.xlsx',)

        self.report.result_query = aql_query

    def run_report(self, sender) -> None:
        self.report.run_report(sender=sender)
