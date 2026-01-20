from DQReport import DQReport


class Report0030:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0030',
                               title='Netwerkelementen hebben een (afgeleide) locatie',
                               spreadsheet_id='1ZAZ8chzMbLEyGd-cbZM6S7Uw4aNOrBmAE1KWnbyvdK4',
                               datasource='PostGIS',
                               persistent_column='G',
                               link_type='eminfra')

        self.report.result_query = """
        select
            a."uuid"
            , a.actief 
            , a.toestand 
            , a.naam 
            , at."label" 
            , g.wkt_string 
        from assets a
        left join assettypes at on a.assettype = at."uuid"
        left join geometrie g on a."uuid" = g.assetuuid
        where
            a.actief is true
            and a.assettype = 'b6f86b8d-543d-4525-8458-36b498333416' -- Netwerkelement (OTL)
            and g.geometry is null
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)

aql_query = """
LET netwerkelement_key = FIRST(FOR at IN assettypes FILTER at.short_uri == "onderdeel#Netwerkelement" LIMIT 1 RETURN at._key)

FOR a IN assets
  FILTER
    a.AIMDBStatus_isActief == true
    AND a.assettype_key == netwerkelement_key
    AND (a.geometry == null OR LENGTH(a.geometry) == 0)

  RETURN {
    uuid: a._key,
    actief: a.AIMDBStatus_isActief,
    toestand: a.toestand,
    naam: a.AIMNaamObject_naam,
    geometry: a.geometry
  }
"""
