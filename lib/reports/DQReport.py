import logging
from datetime import datetime, date, timedelta, UTC
from typing import Any

from googleapiclient.errors import HttpError

from lib.mail.MailSender import MailSender
from lib.reports.Report import Report
from outputs.sheets_cell import SheetsCell
from outputs.sheets_wrapper import SingleSheetsWrapper, SheetsWrapper
from factories import make_datasource, make_output
from outputs.base import OutputWriteContext


class DQReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '',
                 add_filter: bool = True, persistent_column: str = '', frequency: int = 1,
                 convert_columns_to_numbers: list | None = None, link_type: str = 'awvinfra',
                 recalculate_cells: list[tuple[str, str]] | None = None,
                 output: str = 'GoogleSheets', output_settings: dict | None = None):
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
        self.output = output
        self.output_settings = output_settings or {}

    def run_report(self, startcell: str = 'A1', sender: MailSender = None):
        logging.info(f'start running report {self.name}: {self.title}')

        # Resolve adapters
        ds = make_datasource(self.datasource)
        out = make_output(self.output, settings=self.output_settings)

        # test connection first before proceeding with the report
        ds.test_connection()

        sheets_wrapper = SingleSheetsWrapper.get_wrapper()

        # read mail receivers (unchanged behavior)
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

        previous_result, latest_data_sync = self.get_historiek_record_info(sheets_wrapper)

        # persistent column (unchanged logic): read existing values from current Resultaat sheet
        if self.persistent_column != '':
            self.persistent_dict = {}

            sheets = sheets_wrapper.get_sheets_in_spreadsheet(spreadsheet_id=self.spreadsheet_id)
            if 'Resultaat' in sheets:
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

        # execute query via datasource adapter
        query_time = None
        self.now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

        if self.datasource == 'Neo4J':
            self.result_query = self.clean_query(self.result_query)

        qr = ds.execute(self.result_query)
        query_time = qr.query_time_seconds
        self.last_data_update = qr.last_data_update or ''

        # write output via output adapter
        ctx = OutputWriteContext(
            spreadsheet_id=self.spreadsheet_id,
            report_title=self.title,
            datasource_name=self.datasource,
            now_utc=self.now,
        )
        out.write_report(
            ctx,
            qr,
            startcell=startcell,
            add_filter=self.add_filter,
            persistent_column=self.persistent_column,
            persistent_dict=self.persistent_dict,
            convert_columns_to_numbers=self.convert_columns_to_numbers,
            link_type=self.link_type,
            recalculate_cells=self.recalculate_cells,
        )

        # historiek (keep existing Google Sheets behavior)
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
                                           data=[[self.now, self.last_data_update, len(qr.rows)]])

        # summary sheet (unchanged)
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
                                           data=[[self.last_data_update, len(qr.rows)]])

        # also write the query execution time into column H for this report's summary row
        try:
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id,
                                               sheet_name='Overzicht',
                                               start_cell='H' + str(rowFound + 1),
                                               data=[[query_time]])
        except Exception:
            pass

        if mail_receivers is not None:
            self.send_mails(sender=sender, named_range=mail_receivers, previous_result=previous_result,
                            result=len(qr.rows), latest_data_sync=self.last_data_update)

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
                # treat a row as empty if all columns are None or ''
                all_empty = True
                for column in row:
                    if column is not None and column != '':
                        all_empty = False
                        break
                if all_empty:
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

    def send_mails(self, sender: MailSender, named_range: list[list[Any]], previous_result: int, result: int,
                   latest_data_sync: str = ''):
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

    def get_historiek_record_info(self, sheets_wrapper: SheetsWrapper) -> tuple[int | None, str]:
        results = sheets_wrapper.read_data_from_sheet(spreadsheet_id=self.spreadsheet_id, sheet_name='Historiek',
                                                      sheetrange='B2:C2')

        if len(results) == 0:
            return None, ''
        latest_sync = results[0][0]
        previous_count = results[0][1]
        return int(previous_count), latest_sync

    def transform_raw_to_dict(self, mail_receivers_raw) -> list[dict[str, Any]]:
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
