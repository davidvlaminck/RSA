from lib.reports.DQReport import DQReport


class Report0038:
    def __init__(self):
        self.report = None

    def init_report(self):
        aql_query = """
LET ip_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#IP\" LIMIT 1 RETURN at._key)
LET tt_key = FIRST(FOR at IN assettypes FILTER at.short_uri == \"lgc:installatie#TT\" LIMIT 1 RETURN at._key)

FOR i IN assets
  FILTER
    i.assettype_key == ip_key
    AND i.AIMDBStatus_isActief == true
    AND CONTAINS(i.AIMNaamObject_naam, ".AS1")

  LET splitted = SPLIT(i.AIMNaamObject_naampad, "/")
  LET naampad_beh = (
    LENGTH(splitted) > 1 ?
      CONCAT_SEPARATOR("/", SLICE(splitted, 0, LENGTH(splitted) - 1)) + "/" :
      i.AIMNaamObject_naampad
  )

  LET tt_exists = LENGTH(
    FOR t IN assets
      FILTER
        t.assettype_key == tt_key
        AND t.AIMDBStatus_isActief == true
        AND CONTAINS(t.AIMNaamObject_naampad, naampad_beh)
        AND CONTAINS(t.AIMNaamObject_naam, "ODF")
      LIMIT 1
      RETURN t
  ) > 0

  FILTER NOT tt_exists

  RETURN {
    uuid: i._key,
    naampad: i.AIMNaamObject_naampad,
    toezichter: i[\"tz:toezichter.tz:gebruikersnaam\"]
  }
"""
        self.report = DQReport(name='report0038',
                               title="IP AS1 elementen hebben een .ODF TT tegenhanger",
                               spreadsheet_id='1rDCUE7kj0ZcCVtFe2EiIqKMz7fdR5J6mtpU6lRpzpbI',
                               datasource='ArangoDB',
                               persistent_column='D')

        self.report.result_query = aql_query
        self.report.cypher_query = """MATCH (i:IP {isActief:TRUE})\n        WHERE i.naam contains '.AS1'\n        WITH i, split(i.naampad,'/') AS splitted\n        WITH i, apoc.text.join(reverse(tail(reverse(splitted))),'/') + '/' AS naampad_beh\n        OPTIONAL MATCH (t:TT {isActief:TRUE})\n        WHERE t.naampad contains naampad_beh AND t.naam contains 'ODF'\n        WITH i, t\n        WHERE t.uuid IS NULL\n        RETURN i.uuid, i.naampad, i.`tz:toezichter.tz:gebruikersnaam` AS toezichter"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
