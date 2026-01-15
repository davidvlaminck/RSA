from DQReport import DQReport


class Report0012:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0012',
                               title='Camera\'s hebben een Bevestiging relatie tenzij ze tot een tunnel behoren',
                               spreadsheet_id='1ZHc-mdiViQlOKTUtcR_vzvk-DyFiqhwUv5Gf52Q6bm4',
                               datasource='Neo4J',
                               persistent_column='G')

        # TODO recheck query
        self.report.result_query = """OPTIONAL MATCH (c:Camera {isActief:TRUE})-[:HoortBij]->(i:installatie {isActief:TRUE})
        WHERE c IS NOT NULL AND NOT EXISTS((c)-[:Bevestiging]-()) AND NOT i.naampad CONTAINS "TUNNEL" AND NOT i.naampad CONTAINS "Tunnel"
        RETURN c.uuid AS camera_uuid, c.naam AS camera_naam, i.uuid AS installatie_uuid, i.naam AS installatie_naam, i.naampad AS installatie_naampad, i.typeURI"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET camera_assettype_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Camera" LIMIT 1 RETURN at._key)
LET bevestiging_key = FIRST(FOR rt IN relatietypes FILTER rt.short == "Bevestiging" LIMIT 1 RETURN rt._key)

FOR c IN assets
  FILTER
    c.assettype_key == camera_assettype_key
    AND c.AIMDBStatus_isActief == true

  LET has_bevestiging = LENGTH(
    FOR v, e IN 1..1 ANY c._id assetrelaties
      FILTER
        e.relatietype_key == bevestiging_key
        AND v.AIMDBStatus_isActief == true
      LIMIT 1
      RETURN 1
  ) > 0

  FILTER NOT has_bevestiging
    AND NOT CONTAINS(LOWER(TO_STRING(c.NaampadObject_naampad)), "tunnel")

  RETURN {
    camera_uuid: c._key,
    camera_naam: c.AIMNaamObject_naam,
    camera_naampad: c.NaampadObject_naampad,
    camera_typeURI: c.typeURI
  }
"""