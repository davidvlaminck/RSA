from Neo4JConnector import SingleNeo4JConnector
from Report import Report
from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '', add_filter: bool = True):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource, add_filter=add_filter)

    def run_report(self, startcell: str ='A1'):
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        # get and format data
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
            empty_row_nr = sheets_wrapper.find_first_empty_row_from_starting_cell(spreadsheet_id=self.spreadsheet_id,
                                                                                  sheet_name='Resultaat',
                                                                                  start_cell=startcell)
            empty_row = [''] * len(result_keys)
            while len(result) < empty_row_nr:
                result.append(empty_row)

            # write data to Resultaat sheet
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id,
                                               sheet_name='Resultaat',
                                               start_cell=startcell,
                                               data=result)

            # bells and whistles
            # filter
            if self.add_filter:
                sheets_wrapper.clear_filter(self.spreadsheet_id, 'Resultaat')
                start_sheetcell = SheetsCell(startcell)
                end_sheetcell = start_sheetcell.copy()
                end_sheetcell.update_row_by_adding_number(empty_row_nr-2)
                end_sheetcell.update_column_by_adding_number(len(result_keys))
                sheets_wrapper.create_basic_filter(self.spreadsheet_id, 'Resultaat', f'{start_sheetcell.cell}:{end_sheetcell.cell}')

            # hyperlink

            # persist the last column

            # historiek

            # summary sheet


