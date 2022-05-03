import logging
import time
from datetime import datetime

from neo4j.time import DateTime

from Neo4JConnector import SingleNeo4JConnector
from Report import Report
from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '', add_filter: bool = True,
                 persistent_column: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource, add_filter=add_filter)
        self.last_data_update = ''
        self.now = ''
        self.persistent_column = persistent_column
        self.persistent_dict = {}

    def run_report(self, startcell: str = 'A1'):
        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        start_sheetcell = SheetsCell(startcell)

        # persistent column
        if self.persistent_column != '':
            # find first non empty row
            first_cell = SheetsCell(self.persistent_column + '1')
            first_nonempty_row = sheets_wrapper.find_first_nonempty_row_from_starting_cell(spreadsheet_id=self.spreadsheet_id,
                                                                                           sheet_name='Resultaat',
                                                                                           start_cell=first_cell.cell)
            sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id)
            grid_props = sheets['Resultaat']['gridProperties']
            max_row = grid_props['rowCount']

            ids = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                      sheet_name='Resultaat',
                                                      sheetrange='A' + str(first_nonempty_row) + ':A' + str(max_row))
            persisent_column_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                        sheet_name='Resultaat',
                                                                        sheetrange=self.persistent_column + str(
                                                                            first_nonempty_row) + ':' + self.persistent_column + str(
                                                                            max_row))
            self.persistent_dict = {}
            combined_list = zip(ids, persisent_column_data)
            for id, persistent_item in combined_list:
                if id != [] and id[0] != '' and persistent_item != [] and persistent_item[0] != '':
                    self.persistent_dict[id[0]] = persistent_item[0]

        # create a new sheet
        sheets_wrapper.rename_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat',
                                    new_sheet_name='ResultaatDeleteMe')
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
            start = time.time()
            with connector.driver.session() as session:
                query_result = session.run(self.result_query)
                result_keys = query_result.keys()
                result_data = query_result.data()
            end = time.time()
            query_time = round(end - start, 2)
            logging.info(f'fetched query result for {self.name} in {query_time} seconds.')

            headerrow = []
            for key in result_keys:
                header = key.split('.')[1]
                headerrow.append(header)
            if self.persistent_column != '':
                headerrow.append('opmerkingen (blijvend)')
            result.append(headerrow)

            for data in result_data:
                row = []
                for key in result_keys:
                    row.append(data[key])
                if self.persistent_column != '':
                    if row[0] in self.persistent_dict:
                        row.append(self.persistent_dict[row[0]])
                    else:
                        row.append('')
                result.append(row)

            empty_row = [''] * len(result_keys)
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
                end_sheetcell.update_column_by_adding_number(len(result_keys))
                end_sheetcell.update_row_by_adding_number(len(result))
                sheets_wrapper.create_basic_filter(self.spreadsheet_id, 'Resultaat',
                                                   f'{start_sheetcell.cell}:{end_sheetcell.cell}')

            # freeze top rows
            sheets_wrapper.freeze_top_rows(spreadsheet_id=self.spreadsheet_id,
                                           sheet_name='Resultaat',
                                           rows=start_sheetcell.row)

            # shorten typeURI
            type_key = next((k for k in result_keys if 'typeURI' in k), None)
            if type_key is not None:
                typeIndex = result_keys.index(type_key)
                new_type_result = []
                for data in result_data:
                    text = data[type_key].replace('https://wegenenverkeer.data.vlaanderen.be/ns/', '')
                    link = data[type_key]
                    formula = f'=HYPERLINK("{link}"; "{text}")'
                    new_type_result.append(formula)
                typeUri_sheetcell = start_sheetcell.copy()
                typeUri_sheetcell.update_column_by_adding_number(typeIndex)
                typeUri_sheetcell.update_row_by_adding_number(1)
                sheets_wrapper.write_formulae_cells(spreadsheet_id=self.spreadsheet_id,
                                                    sheet_name='Resultaat',
                                                    start_cell=typeUri_sheetcell.cell,
                                                    formulae=new_type_result)

            # make columns fit to the data
            sheets_wrapper.automatic_resize_columns(spreadsheet_id=self.spreadsheet_id,
                                                    sheet_name='Resultaat',
                                                    number_of_columns=len(result_keys))

            # hyperlink the first column
            start_sheetcell.update_row_by_adding_number(1)
            first_column = list(map(lambda x: x[0], result[1:]))
            sheets_wrapper.add_hyperlink_column(spreadsheet_id=self.spreadsheet_id,
                                                sheet_name='Resultaat',
                                                start_cell=start_sheetcell.cell,
                                                link_type='onderdeel',
                                                column_data=first_column)

            # historiek
            historiek_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                 sheet_name='Historiek',
                                                                 sheetrange='B2:B2')
            last_data_update = None
            if len(historiek_data) > 0:
                last_data_update = historiek_data[0][0]
            if last_data_update != self.last_data_update:
                sheets_wrapper.insert_empty_rows(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                                 number_of_rows=1)
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek', start_cell='A2',
                                               data=[[self.now, self.last_data_update, len(result_data)]])

            # summary sheet
            summary_links = sheets_wrapper.read_celldata_from_sheet(spreadsheet_id=self.summary_sheet_id, sheet_name='Overzicht',
                                                                    sheetrange='B4:B')
            rowFound = summary_links['startRow']
            for i, summary_link in enumerate(summary_links['rowData']):
                if 'values' not in summary_link:
                    continue
                if 'hyperlink' not in summary_link['values'][0]:
                    continue
                if self.spreadsheet_id in summary_link['values'][0]['hyperlink']:
                    rowFound += i
                    break
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id,
                                               sheet_name='Overzicht',
                                               start_cell='C' + str(rowFound + 1),
                                               data=[[self.last_data_update]])
