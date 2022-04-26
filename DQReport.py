from Neo4JConnector import SingleNeo4JConnector
from Report import Report
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource)

    def run_report(self):
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        sheets_wrapper.create_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatNieuw')

        result = []
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session() as session:
                query_result = session.run(self.result_query)
                result_keys = query_result.keys()
                result_data = query_result.data()

                headerrow = []
                for key in result_keys:
                    header = key.split('.')[1]
                    headerrow.append(header)
                result.append(headerrow)

                for data in result_data:
                    row = []
                    for key in result_keys:
                        row.append(data[key])
                    result.append(row)

        # clear data by
        # get row range from headerrow
        # get first non empty by getting first n rows 200 - 1000 - 5000 - 2500 (* 5)

        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatNieuw', start_cell='A1', data=result)



        print('init of a sheetswrapper succeeded')