from DQReport import DQReport


class Report0059:
    def __init__(self):
        self.report = None

    def init_report(self):
        self.report = DQReport(name='report0059',
                               title='Er zijn geen assets die zichzelf direct of indirect voeden (geen lussen in voeding).',
                               spreadsheet_id='15z-3mTVmjg63EepO1uaN5R5dgFARcfiyrRBbXa3TzUQ',
                               datasource='Neo4J',
                               persistent_column='F')

        self.report.result_query = """
            MATCH p=(x:Asset {isActief: True})-[:Voedt*]->(x)
            WITH x, reduce(path_loop = [], n IN nodes(p) | path_loop + [[n.uuid, n.typeURI]]) as path_loop
            RETURN DISTINCT x.uuid AS uuid, x.naampad AS naampad, x.typeURI AS typeURI, x.toestand as toestand, path_loop
        """

    def run_report(self, sender):
        self.report.run_report(sender=sender)
