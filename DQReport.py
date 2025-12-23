import decimal
import logging
import time
from datetime import datetime, date, timedelta

from googleapiclient.errors import HttpError
from neo4j.time import DateTime

from MailSender import MailSender
from Neo4JConnector import SingleNeo4JConnector
from PostGISConnector import SinglePostGISConnector
from Report import Report
from SheetsCell import SheetsCell
from SheetsWrapper import SingleSheetsWrapper, SheetsWrapper


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '',
                 add_filter: bool = True, persistent_column: str = '', frequency: int = 1,
                 convert_columns_to_numbers: list = None, link_type: str = 'awvinfra',
                 recalculate_cells: [(str, str)] = None):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource, add_filter=add_filter,
                        frequency=frequency)
        self.last_data_update = ''
        self.now = ''
        self.link_type = link_type
        self.recalculate_cells = recalculate_cells
        if self.recalculate_cells is None:
            self.recalculate_cells = []
        self.persistent_column = persistent_column
        self.persistent_dict = {}
        if convert_columns_to_numbers is None:
            self.convert_columns_to_numbers = []
        else:
            self.convert_columns_to_numbers = convert_columns_to_numbers

    def run_report(self, startcell: str = 'A1', sender: MailSender = None):
        logging.info(f'start running report {self.name}: {self.title}')

         # testing connection first before proceeding with the report
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session(database=connector.db) as session:
                query_result: DateTime = session.run('MATCH (p:Params) RETURN p.last_update_utc').single()[0]
        elif self.datasource == 'PostGIS':
            connector = SinglePostGISConnector.get_connector()
            params = connector.get_params(connector.main_connection)

        sheets_wrapper = SingleSheetsWrapper.get_wrapper()
        start_sheetcell = SheetsCell(startcell)

        # TODO
        # determine to run or not, based on frequency
        # use summary sheet and self.frequence in days

        mail_receivers = None
        try:
            mail_receivers_raw = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Overzicht',
                                                                 sheetrange='emails', return_raw_results=True)
            mail_receivers = mail_receivers_raw.get('values', [])
            mail_receivers_dict = self.transform_raw_to_dict(mail_receivers_raw)
            sender.add_sheet_info(spreadsheet_id=self.spreadsheet_id, mail_receivers_dict=mail_receivers_dict)
        except HttpError as exc:
            if exc.error_details == 'Unable to parse range: Overzicht!emails':
                logging.info(f'{self.__class__.__name__} does not have a range Overzicht!emails')
            else:
                raise exc
                # skip sending mails

        previous_result, latest_data_sync = self.get_historiek_record_info(sheets_wrapper)

        # persistent column
        if self.persistent_column != '':
            self.persistent_dict = {}

            # check if there is a Resultaat sheet, only proceed when it does
            sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id)
            if 'Resultaat' in sheets:

                # find first non empty row
                first_cell = SheetsCell(self.persistent_column + '1')
                first_nonempty_row = sheets_wrapper.find_first_nonempty_row_from_starting_cell(spreadsheet_id=self.spreadsheet_id,
                                                                                               sheet_name='Resultaat',
                                                                                               start_cell=first_cell.cell)

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

                combined_list = zip(ids, persisent_column_data)
                for id, persistent_item in combined_list:
                    if id != [] and id[0] != '' and persistent_item != [] and persistent_item[0] != '':
                        self.persistent_dict[id[0]] = persistent_item[0]

        # create a new sheet
        sheets_wrapper.delete_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatRenameMe')
        sheets_wrapper.create_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatRenameMe')
        sheets_wrapper.delete_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat')
        sheets_wrapper.rename_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='ResultaatRenameMe',
                                    new_sheet_name='Resultaat')

        # add first rule: when is the report made and when is the used data last sync'd
        if self.datasource == 'Neo4J':
            connector = SingleNeo4JConnector.get_connector()
            with connector.driver.session(database=connector.db) as session:
                query_result: DateTime = session.run('MATCH (p:Params) RETURN p.last_update_utc').single()[0]

            self.last_data_update = query_result.to_native().strftime("%Y-%m-%d %H:%M:%S")
            self.now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            report_made_lines = [[f'Rapport gemaakt op {self.now} met data uit:'],
                                 [f'{self.datasource}, laatst gesynchroniseerd op {self.last_data_update}']]
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat', start_cell=startcell,
                                               data=report_made_lines)
            start_sheetcell.update_row_by_adding_number(len(report_made_lines))
        elif self.datasource == 'PostGIS':
            connector = SinglePostGISConnector.get_connector()

            params = connector.get_params(connector.main_connection)

            self.last_data_update = params['last_update_utc_assets'].strftime("%Y-%m-%d %H:%M:%S")
            self.now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            report_made_lines = [[f'Rapport gemaakt op {self.now} met data uit:'],
                                 [f'{self.datasource}, laatst gesynchroniseerd op {self.last_data_update}']]
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Resultaat',
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

        result_data = self.clean(result_data, headerrow=result_keys)

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

        # convert specified columns to numbers
        col_indices = []
        for col in self.convert_columns_to_numbers:  # columns
            col_indices.append(SheetsCell(col + '1')._column_int - 1)
        if len(col_indices) > 0:
            for row_index, result_row in enumerate(result):
                if row_index == 0:
                    continue
                for col_index in col_indices:
                    value = result[row_index][col_index]
                    if value is not None and value != 'None':
                        result[row_index][col_index] = float(result[row_index][col_index])

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
            end_sheetcell.update_row_by_adding_number(len(result) - 1)
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
                if data[typeIndex] is not None and data[typeIndex] != '':
                    text = data[typeIndex].replace('https://wegenenverkeer.data.vlaanderen.be/ns/', '') \
                        .replace('https://lgc.data.wegenenverkeer.be/ns/', '')
                    link = data[typeIndex]
                    formula = f'=HYPERLINK("{link}"; "{text}")'
                    new_type_result.append(formula)
                else:
                    for col in data:
                        if col is not None and col != '':
                            new_type_result.append('')
                            break

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
                                            link_type=self.link_type,
                                            column_data=first_column)

        # recalculate formulas
        for formula_location in self.recalculate_cells:
            sheets_wrapper.recalculate_formula(sheet_name=formula_location[0], spreadsheet_id=self.spreadsheet_id,
                                               cell=formula_location[1])

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
                                           data=[[self.last_data_update, len(result_data)]])

        if mail_receivers is not None:
            self.send_mails(sender=sender, named_range=mail_receivers, previous_result=previous_result,
                            result=len(result_data), latest_data_sync=self.last_data_update)

        logging.info(f'finished report {self.name}')

    @staticmethod
    def clean(result_data, headerrow: list[str]):
        """Removes the empty rows in the results, converts lists, decimals and dates to strings """
        new_result_data = []

        for row in result_data:
            if isinstance(row, dict):
                row = [row.get(key, '') for key in headerrow]

            if isinstance(row, tuple):
                row = list(row)

            if isinstance(row, list):
                all_none = True
                for column in row:
                    if column is not None or column != '':
                        all_none = False
                        break
                if all_none:
                    continue

            new_row = []
            for column in row:
                if column is None:
                    new_row.append(None)
                elif not isinstance(column, str):
                    if isinstance(column, datetime):
                        new_row.append(column.strftime('%Y-%m-%d %H:%M:%S'))
                    elif isinstance(column, date):
                        new_row.append(column.strftime('%Y-%m-%d'))
                    elif isinstance(column, list):
                        new_row.append(DQReport.make_list_into_strings(column))
                    else:
                        new_row.append(str(column))
                else:
                    new_row.append(column)
            row = new_row

            new_result_data.append(row)
        return new_result_data

    def send_mails(self, sender: MailSender, named_range: [list], previous_result: int, result: int, latest_data_sync: str = ''):
        if len(named_range) == 0:
            return

        for line in named_range:
            if line is None or len(line) < 2 or line[0] == '' or line[0] is None:
                continue
            if line[1] == 'Wijziging':
                if previous_result != result:
                    sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                    count=result, latest_sync=latest_data_sync, frequency=line[1],
                                    previous = previous_result)
                    # add frequency
            elif line[1] in ['Dagelijks', 'Wekelijks', 'Maandelijks', 'Jaarlijks']:
                if len(line) < 3 or line[2] == '' or line[2] is None:
                    sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                    count=result, latest_sync=latest_data_sync, frequency=line[1],
                                    previous = previous_result)
                else:
                    dt = datetime.strptime(line[2], '%Y-%m-%d %H:%M:%S')
                    last_sent = dt.date()
                    if line[1] == 'Dagelijks':
                        diff_days = date.today() - last_sent
                        if diff_days >= timedelta(days=1):
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Wekelijks':
                        diff_days = date.today() - last_sent
                        if diff_days >= timedelta(days=7):
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Maandelijks':
                        current_month = date.today().month
                        if current_month != last_sent.month:
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])
                    elif line[1] == 'Jaarlijks':
                        current_month = date.today().year
                        if current_month != last_sent.year:
                            sender.add_mail(receiver=line[0], report_name=self.title, spreadsheet_id=self.spreadsheet_id,
                                            count=result, latest_sync=latest_data_sync, frequency=line[1])

    def get_historiek_record_info(self, sheets_wrapper: SheetsWrapper) -> (int, str):
        results = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                                      sheetrange='B2:C2')

        if len(results) == 0:
            return None, ''
        latest_sync = results[0][0]
        previous_count = results[0][1]
        return int(previous_count), latest_sync

    def transform_raw_to_dict(self, mail_receivers_raw) -> [dict]:
        mail_dicts = []
        sheetrange = mail_receivers_raw['range'].split('!')[1]
        cells = sheetrange.split(':')
        startcell = SheetsCell(cells[0])
        startcell.update_column_by_adding_number(2)
        if 'values' not in mail_receivers_raw:
            return mail_dicts
        for list_element in mail_receivers_raw['values']:
            if len(list_element) < 2:
                if len(list_element) > 0 and list_element[0] == '':
                    continue
                raise ValueError("not correctly configured mailing template")

            mail_dict = {}
            mail_dicts.append(mail_dict)
            mail_dict['mail'] = list_element[0]
            mail_dict['frequency'] = list_element[1]
            mail_dict['cell'] = startcell.cell
            if len(list_element) > 2:
                mail_dict['last_update'] = list_element[2]

            startcell.row += 1

        return mail_dicts

    def clean_query(self, query):
        query_lines = query.split('\n')
        new_q = []
        for line in query_lines:
            if '//' not in line:
                new_q.append(line)
            else:
                new_q.append(line.split('//')[0])
        return '\n'.join(new_q)

    @classmethod
    def make_list_into_strings(cls, data: list, sep: str = '|'):
        if not isinstance(data, list):
            return data
        for index, value in enumerate(data):
            if isinstance(value, list):
                value = cls.make_list_into_strings(value, sep = f'|{sep}')
                data[index] = value
        return sep.join([str(d) for d in data])





