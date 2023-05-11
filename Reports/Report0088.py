from DQReport import DQReport


class Report0088:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0088',
                               title='VRI Wegkantkasten hebben een afmeting',
                               spreadsheet_id='1WgLd7ESfGiJadbfALzJEwNG2-dNhUZALltPqk9WTynw',
                               datasource='Neo4J',
                               persistent_column='F')

        self.report.result_query = """MATCH (k:Wegkantkast {isActief:TRUE})-[:Bevestiging]-(vr:Verkeersregelaar {isActief:TRUE}) 
WHERE vr IS NOT NULL AND (k.`afmeting.lengte` IS NULL OR k.`afmeting.breedte` IS NULL OR k.`afmeting.hoogte` IS NULL OR (CASE WHEN k.`afmeting.breedte` < k.`afmeting.lengte` AND k.`afmeting.breedte`< k.`afmeting.hoogte` THEN TRUE ELSE FALSE END) = FALSE)
RETURN k.uuid, k.naam, k.`afmeting.lengte`, k.`afmeting.breedte`, k.`afmeting.hoogte`"""

    def run_report(self, sender):
        self.report.run_report(sender=sender)
