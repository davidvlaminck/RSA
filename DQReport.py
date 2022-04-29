from datetime import datetime

from neo4j.time import DateTime

from Neo4JConnector import SingleNeo4JConnector
from Report import Report
from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '', add_filter: bool = True):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource, add_filter=add_filter)
        self.last_data_update = ''
        self.now = ''

    def run_report(self, startcell: str = 'A1'):
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        start_sheetcell = SheetsCell(startcell)

        sheets_wrapper.rename_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat', new_sheet_name='ResultaatDeleteMe')
        sheets_wrapper.create_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat')
        sheets_wrapper.delete_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatDeleteMe')

        # add first rule: when made and when was the data last sync'd
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session() as session:
                query_result: DateTime = session.run('MATCH (p:Params) RETURN p.last_update_utc').single()[0]

            self.last_data_update = query_result.to_native().strftime("%Y-%m-%d %H:%M:%S")
            self.now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            report_made_lines = [[f'Rapport gemaakt op {self.now} met data uit:'],
                                 [f'{self.datasource}, laatst gesynchroniseerd op {self.last_data_update}']]
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat', start_cell=startcell,
                                               data=report_made_lines)
            start_sheetcell.update_row_by_adding_number(len(report_made_lines))

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
                                                                                  start_cell=start_sheetcell.cell)
            empty_row = [''] * len(result_keys)
            while len(result) + start_sheetcell.row <= empty_row_nr:
                result.append(empty_row)

            # write data to Resultaat sheet
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id,
                                               sheet_name='Resultaat',
                                               start_cell=start_sheetcell.cell,
                                               data=result)

            # bells and whistles
            # filter
            if self.add_filter:
                sheets_wrapper.clear_filter(self.spreadsheet_id, 'Resultaat')
                end_sheetcell = start_sheetcell.copy()
                end_sheetcell.row = empty_row_nr - 1
                end_sheetcell.update_column_by_adding_number(len(result_keys))
                sheets_wrapper.create_basic_filter(self.spreadsheet_id, 'Resultaat',
                                                   f'{start_sheetcell.cell}:{end_sheetcell.cell}')

            # freeze top rows
            sheets_wrapper.freeze_top_rows(spreadsheet_id=self.spreadsheet_id,
                                           sheet_name='Resultaat',
                                           rows=start_sheetcell.row)

            # hyperlink
            start_sheetcell.update_row_by_adding_number(1)
            first_column = list(map(lambda x: x[0], result[1:]))
            sheets_wrapper.add_hyperlink_column(spreadsheet_id=self.spreadsheet_id,
                                                sheet_name='Resultaat',
                                                start_cell=start_sheetcell.cell,
                                                link_type='onderdeel',
                                                column_data=first_column)

            # persist the last column

            # historiek
            last_data_update = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                                                   sheetrange='B2:B2')[0][0]
            if last_data_update != self.last_data_update:
                sheets_wrapper.insert_empty_rows(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                                 number_of_rows=1)
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                               data=[[self.now, self.last_data_update, len([1, 2, 3])]])

            # summary sheet
