import decimal
import logging
import time
from datetime import datetime, date, timedelta

from neo4j.time import DateTime

from MailSender import MailSender
from Neo4JConnector import SingleNeo4JConnector
from PostGISConnector import SinglePostGISConnector
from Report import Report
from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper


class LegacyHistoryReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '',
                 add_filter: bool = True, frequency: int = 1, persistent_column: str = '', sheets_to_keep: int = 5,
                 sheet_name: str = '', sheets_to_ignore: [str] = None):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource,
                        add_filter=add_filter,
                        frequency=frequency)
        self.sheet_name = sheet_name
        self.persistent_column = persistent_column
        self.persistent_dict = {}
        self.sheets_to_keep = sheets_to_keep
        if sheets_to_ignore is None:
            self.sheets_to_ignore = []
        else:
            self.sheets_to_ignore = sheets_to_ignore

        self.last_data_update = ''
        self.now = ''

    def run_report(self, startcell: str = 'A1', sender=None):
        logging.info(f'start running report {self.name}: {self.title}')

        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        start_sheetcell = SheetsCell(startcell)

        # determine to run or not, based on frequency
        # use summary sheet and self.frequency in days
        # summary sheet
        summary_links = sheets_wrapper.read_celldata_from_sheet(spreadsheet_id=self.summary_sheet_id,
                                                                sheet_name='Overzicht',
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

        summary_last_update_cell = SheetsCell('C' + str(rowFound + 1))
        last_update_cell = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.summary_sheet_id,
                                                               sheet_name='Overzicht',
                                                               sheetrange=summary_last_update_cell.cell + ':' +
                                                                          summary_last_update_cell.cell)

        if len(last_update_cell) == 0 or last_update_cell[0][0] == '':
            pass
        else:
            last_update_str = last_update_cell[0][0]
            dt = datetime.strptime(last_update_str, '%Y-%m-%d %H:%M:%S')
            last_updated = dt.date()
            diff_days = date.today() - last_updated
            if diff_days >= timedelta(days=self.frequency):
                pass
            else:
                logging.info(
                    f'This report ran on {last_update_str}. Running this now would violate the frequency rule: run '
                    f'once every {self.frequency} days')
                return

        # find sheets:
        # determine and set latest sheet if possible
        # remove all sheets except for 'Historiek' and the 5 latest sheets
        sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id).keys()
        sheet_names = [sheet_key for sheet_key in sheets]
        sheet_names.remove('Historiek')
        for sheet_to_ignore in self.sheets_to_ignore:
            if sheet_to_ignore in sheet_names:
                sheet_names.remove(sheet_to_ignore)
        sheet_names = list(reversed(sorted(sheet_names, key=lambda x: datetime.strptime(x, '%d/%m/%Y'))))

        lastest_sheetname = None
        if len(sheet_names) > 0:
            lastest_sheetname = sheet_names[0]
        new_sheetname = datetime.utcnow().strftime('%d/%m/%Y')

        if len(sheet_names) > self.sheets_to_keep:
            for delete_name in sheet_names[self.sheets_to_keep:]:
                sheets_wrapper.delete_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name=delete_name)
        if new_sheetname not in sheet_names:
            # TODO create at index 1 (after Historiek)
            sheets_wrapper.create_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name=new_sheetname)

        # persistent column
        if self.persistent_column != '':
            # find first non empty row
            first_cell = SheetsCell(self.persistent_column + '1')
            first_nonempty_row = sheets_wrapper.find_first_nonempty_row_from_starting_cell(
                spreadsheet_id=self.spreadsheet_id,
                sheet_name=lastest_sheetname,
                start_cell=first_cell.cell)
            sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id)
            grid_props = sheets[lastest_sheetname]['gridProperties']
            max_row = grid_props['rowCount']

            ids = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                      sheet_name=lastest_sheetname,
                                                      sheetrange='A' + str(first_nonempty_row) + ':A' + str(
                                                          max_row))
            persisent_column_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                                        sheet_name=lastest_sheetname,
                                                                        sheetrange=self.persistent_column + str(
                                                                            first_nonempty_row) + ':' + self.persistent_column + str(
                                                                            max_row))
            self.persistent_dict = {}
            combined_list = zip(ids, persisent_column_data)
            for id, persistent_item in combined_list:
                if id != [] and id[0] != '' and persistent_item != [] and persistent_item[0] != '':
                    self.persistent_dict[id[0]] = persistent_item[0]

        # add first rule: when is the report made and when is the used data last sync'd
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session(database=connector.db) as session:
                query_result: DateTime = session.run('MATCH (p:Params) RETURN p.last_update_utc').single()[0]

            self.last_data_update = query_result.to_native().strftime("%Y-%m-%d %H:%M:%S")
            self.now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            report_made_lines = [[f'Rapport gemaakt op {self.now} met data uit:'],
                                 [f'{self.datasource}, laatst gesynchroniseerd op {self.last_data_update}']]
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name=new_sheetname,
                                               start_cell=startcell,
                                               data=report_made_lines)
            start_sheetcell.update_row_by_adding_number(len(report_made_lines))
        elif self.datasource == 'PostGIS':
            connector = SinglePostGISConnector.get_connector()

            params = connector.get_params(connector.main_connection)

            self.last_data_update = params['last_update_utc_assets'].strftime("%Y-%m-%d %H:%M:%S")
            self.now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            report_made_lines = [[f'Rapport gemaakt op {self.now} met data uit:'],
                                 [f'{self.datasource}, laatst gesynchroniseerd op {self.last_data_update}']]
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name=new_sheetname,
                                               start_cell=startcell,
                                               data=report_made_lines)
            start_sheetcell.update_row_by_adding_number(len(report_made_lines))

        # get and format data
        result = []
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            start = time.time()
            self.result_query = self.clean_query(self.result_query)
            with connector.driver.session(database=connector.db) as session:
                query_result = session.run(self.result_query)
                result_keys = query_result.keys()
                result_data = query_result.data()
            end = time.time()
            query_time = round(end - start, 2)
            logging.info(f'fetched query result for {self.name} in {query_time} seconds.')

        elif self.datasource == 'PostGIS':
            connector = SinglePostGISConnector.get_connector()

            start = time.time()
            with connector.main_connection.cursor() as cursor:
                cursor.execute(self.result_query)
                result_data = cursor.fetchall()
                result_keys = list(map(lambda col: col.name, cursor.description))

            end = time.time()
            query_time = round(end - start, 2)
            logging.info(f'fetched query result for {self.name} in {query_time} seconds.')

        headerrow = []
        for key in result_keys:
            if '.' in key:
                header = key.split('.')[1]
            else:
                header = key
            headerrow.append(header)
        if self.persistent_column != '':
            headerrow.append('opmerkingen (blijvend)')
        result.append(headerrow)

        result_data = self.clean(result_data)

        if self.datasource == 'Neo4J':
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
        elif self.datasource == 'PostGIS':
            for data in result_data:
                row = []
                row.extend(data)
                if self.persistent_column != '':
                    if row[0] in self.persistent_dict:
                        row.append(self.persistent_dict[row[0]])
                    else:
                        row.append('')
                result.append(row)

        amount_empty_rows = len(result_keys)
        if self.persistent_column != '':
            amount_empty_rows += 1
        empty_row = [''] * amount_empty_rows
        if len(result) == 0:
            result.append(empty_row)

        # write data to new_sheetname sheet
        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id,
                                           sheet_name=new_sheetname,
                                           start_cell=start_sheetcell.cell,
                                           data=result)

        # bells and whistles
        # filter
        if self.add_filter:
            sheets_wrapper.clear_filter(self.spreadsheet_id, new_sheetname)
            end_sheetcell = start_sheetcell.copy()
            end_sheetcell.update_column_by_adding_number(len(result_keys))
            end_sheetcell.update_row_by_adding_number(len(result) - 1)
            sheets_wrapper.create_basic_filter(self.spreadsheet_id, new_sheetname,
                                               f'{start_sheetcell.cell}:{end_sheetcell.cell}')

        # freeze top rows
        sheets_wrapper.freeze_top_rows(spreadsheet_id=self.spreadsheet_id,
                                       sheet_name=new_sheetname,
                                       rows=start_sheetcell.row)

        # shorten typeURI
        type_key = next((k for k in result_keys if 'typeURI' in k), None)
        if type_key is not None:
            typeIndex = result_keys.index(type_key)
            new_type_result = []
            for data in result_data:
                if data[type_key] is not None and data[type_key] != '':
                    text = data[type_key].replace('https://wegenenverkeer.data.vlaanderen.be/ns/', '') \
                        .replace('https://lgc.data.wegenenverkeer.be/ns/', '')
                    link = data[type_key]
                    formula = f'=HYPERLINK("{link}"; "{text}")'
                    new_type_result.append(formula)
                else:
                    for col in data.values():
                        if col is not None:
                            new_type_result.append('')
                            break

            typeUri_sheetcell = start_sheetcell.copy()
            typeUri_sheetcell.update_column_by_adding_number(typeIndex)
            typeUri_sheetcell.update_row_by_adding_number(1)
            sheets_wrapper.write_formulae_cells(spreadsheet_id=self.spreadsheet_id,
                                                sheet_name=new_sheetname,
                                                start_cell=typeUri_sheetcell.cell,
                                                formulae=new_type_result)

        # make columns fit to the data
        sheets_wrapper.automatic_resize_columns(spreadsheet_id=self.spreadsheet_id,
                                                sheet_name=new_sheetname,
                                                number_of_columns=len(result_keys))

        # hyperlink the first column
        start_sheetcell.update_row_by_adding_number(1)
        first_column = list(map(lambda x: x[0], result[1:]))
        sheets_wrapper.add_hyperlink_column(spreadsheet_id=self.spreadsheet_id,
                                            sheet_name=new_sheetname,
                                            start_cell=start_sheetcell.cell,
                                            link_type='eminfra',
                                            column_data=first_column)

        # historiek
        historiek_data = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id,
                                                             sheet_name='Historiek',
                                                             sheetrange='A5:A5')
        last_data_update = None
        if len(historiek_data) > 0:
            last_data_update = historiek_data[0][0]
        if last_data_update != self.last_data_update:
            sheets_wrapper.insert_empty_rows(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                             start_cell='A5',
                                             number_of_rows=1)

        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                           start_cell='A5',
                                           data=[[self.now, len(result_data), 'Productie']])

        # summary sheet
        summary_links = sheets_wrapper.read_celldata_from_sheet(spreadsheet_id=self.summary_sheet_id,
                                                                sheet_name='Overzicht',
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
                                           data=[[self.last_data_update, len(result_data)]])

        logging.info(f'finished report {self.name}')

    @staticmethod
    def clean(result_data):
        """Removes the empty rows in the results"""
        new_result_data = []

        for data in result_data:
            if isinstance(data, tuple):
                data = list(data)

            if isinstance(data, list):
                all_none = True
                for column in data:
                    if column is not None or column != '':
                        all_none = False
                        break
                if all_none:
                    continue
                new_result_data.append(data)
            elif isinstance(data, dict):
                all_none = True
                for column in data.values():
                    if column is not None and column != '':
                        all_none = False
                        break
                if all_none:
                    continue
                new_result_data.append(data)
            else:
                if data is not None and data != '':
                    new_result_data.append(data)

        result_data = new_result_data
        new_result_data = []
        for row in result_data:
            for index, value in enumerate(row):
                if isinstance(value, decimal.Decimal):
                    row[index] = str(value)

            new_result_data.append(row)

        return new_result_data

    def send_mails(self, sender: MailSender, named_range: [list], previous_result: int, result: int,
                   latest_data_sync: str = ''):
        pass

    def clean_query(self, query):
        query_lines = query.split('\n')
        new_q = []
        for line in query_lines:
            if '//' not in line:
                new_q.append(line)
            else:
                new_q.append(line.split('//')[0])
        return '\n'.join(new_q)
