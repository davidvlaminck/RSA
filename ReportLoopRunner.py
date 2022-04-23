#     exec(open('report1.py').read())

# inhoud
# if __name__ == '__main__':
#     r = Report('report 1')

# initialize a SheetsWrapper throush SingleSheetsWrapper
# same for Neo4JConnector and other connectors
# then run reports that use the Single.. version of the class to get the initiliazed version
from os.path import exists

from Neo4JConnector import SingleNeo4JConnector
from SheetsWrapper import SingleSheetsWrapper


class ReportLoopRunner:
    def __init__(self):
        SingleSheetsWrapper.init(service_cred_path='C:\\resources\\driven-wonder-149715-ca8bdf010930.json',
                                 readonly_scope=False)
        SingleNeo4JConnector.init("bolt://localhost:7687", "neo4jPython", "python")

        self.reports = ['Report0001.py']

    def run(self):
        for report in self.reports:
            exist = exists('Reports/Report0001.py')
            exec(open('Reports\\' + report).read())


if __name__ == '__main__':
    reportlooprunner = ReportLoopRunner()
    reportlooprunner.run()
