from Neo4JConnector import SingleNeo4JConnector
from Report import Report
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource)

    def run_report(self):
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        empty_row_nr = sheets_wrapper.find_first_empty_row_from_starting_cell(spreadsheet_id = self.spreadsheet_id, sheet_name='Resultaat', start_cell='A1')

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

            # add empty rows to clear existing data
            empty_row = [''] * len(result_keys)
            while len(result) < empty_row_nr:
                result.append(empty_row)

        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat', start_cell='A1', data=result)
