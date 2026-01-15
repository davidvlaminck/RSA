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


class LegacyReport(Report):
    def __init__(self, name: str = '', title: str = '', spreadsheet_id: str = '', datasource: str = '',
                 add_filter: bool = True, frequency: int = 1,
                 sheet_name: str = ''):
        Report.__init__(self, name=name, title=title, spreadsheet_id=spreadsheet_id, datasource=datasource,
                        add_filter=add_filter,
                        frequency=frequency)
        self.sheet_name = sheet_name

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
                                                          sheetrange=summary_last_update_cell.cell + ':' + summary_last_update_cell.cell)

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
                logging.info(f'This report ran on {last_update_str}. Running this now would violate the frequency rule: run once every {self.frequency} days')
                return

        # get and format data
        result = []
        query_time = None
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

        result_data = self.clean(result_data)

        if self.datasource == 'Neo4J':
            for data in result_data:
                row = []
                for key in result_keys:
                    row.append(data[key])
                result.append(row)
        elif self.datasource == 'PostGIS':
            for data in result_data:
                row = []
                row.extend(data)
                result.append(row)

        amount_empty_rows = len(result_keys)

        empty_row = [''] * amount_empty_rows
        if len(result) == 0:
            result.append(empty_row)

        empty_row_nr = sheets_wrapper.find_first_empty_row_from_starting_cell(spreadsheet_id=self.spreadsheet_id,
                                                                              sheet_name=self.sheet_name,
                                                                              start_cell=start_sheetcell.cell)

        start_sheetcell.update_row_by_adding_number(empty_row_nr)

        # write data to Resultaat sheet
        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.spreadsheet_id,
                                           sheet_name=self.sheet_name,
                                           start_cell=start_sheetcell.cell,
                                           data=result,
                                           value_input_option='USER_ENTERED')

        # update summary sheet
        sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id,
                                           sheet_name='Overzicht',
                                           start_cell='C' + str(rowFound + 1),
                                           data=[[datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), None]])

        # also write the query execution time into column H for this report's summary row
        try:
            sheets_wrapper.write_data_to_sheet(spreadsheet_id=self.summary_sheet_id,
                                               sheet_name='Overzicht',
                                               start_cell='H' + str(rowFound + 1),
                                               data=[[query_time]])
        except Exception:
            # if query_time is not available for some reason, skip silently to avoid breaking the report
            pass

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
