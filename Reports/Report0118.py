from lib.reports.DQReport import DQReport


class Report0118:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0118',
                               title='Elke installatie heeft een bestekkoppeling',
                               spreadsheet_id='1bpZLWgqFp6AsRqxaTCnvc8IqpnnmSnoajlCABGD4TbY',
                               datasource='PostGIS',
                               persistent_column='E')

        self.report.result_query = """
        with cte_installaties as (
            -- OTL en legacy installaties
            select uuid, naam, label, uri, definitie
            from assettypes
            where uri like ('%https://wegenenverkeer.data.vlaanderen.be/ns/installatie%')
              or uri like ('%https://lgc.data.wegenenverkeer.be/ns/installatie#%')
            order by label
        )
        select
            a.uuid
            , at.uri
            , a.naampad 
            , a.naam
        from cte_installaties inst
        left join assets a on inst.uuid = a.assettype
        left join assettypes at on a.assettype = at."uuid" 
        inner join bestekkoppelingen b on a.uuid = b.assetuuid
        where
          a.actief = true
          and
          b.bestekuuid is null;
                """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
