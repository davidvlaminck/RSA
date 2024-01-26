import json
import socket
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account

from SheetsCell import SheetsCell


class SheetsWrapper:
    def __init__(self, service_cred_path: str = '', readonly_scope: None | bool = None):
        if service_cred_path == '':
            raise NotImplementedError('only access with service account is supported')
        self.service_cred_path = service_cred_path
        self.credentials: None | Credentials = None

        socket.setdefaulttimeout(180)

        if readonly_scope is None:
            raise ValueError('set readonly_scope to True or False')

    def create_sheet(self, spreadsheet_id: str, sheet_name: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [
                {'addSheet':
                     {'properties':
                          {'title': sheet_name}}}]}).execute()

    def delete_sheet(self, spreadsheet_id: str, sheet_name: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        if sheet_name not in sheets:
            return

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [
                {'deleteSheet':
                     {'sheetId': sheets[sheet_name]['sheetId']
                      }}]}).execute()

    def clear_filter(self, spreadsheet_id: str, sheet_name: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests':
                      [{'clearBasicFilter': {"sheetId": sheets[sheet_name]['sheetId']}
                        }]}).execute()

    def create_basic_filter(self, spreadsheet_id: str, sheet_name: str, range: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        start = SheetsCell(range.split(':')[0])
        end = SheetsCell(range.split(':')[1])

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{'setBasicFilter': {
                "filter": {
                    "range": {
                        "sheetId": sheets[sheet_name]['sheetId'],
                        "startRowIndex": start.row - 1,
                        "endRowIndex": end.row,
                        "startColumnIndex": start._column_int - 1,
                        "endColumnIndex": end._column_int
                    }
                }
            }}])).execute()

    def get_sheets_in_spreadsheet(self, spreadsheet_id: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets')
        sheets_dict = {}
        for sheet in sheets:
            sheets_dict[sheet['properties']['title']] = sheet['properties']
        return sheets_dict

    def write_data_to_sheet(self, spreadsheet_id: str, sheet_name: str, start_cell: str, data: list,
                            value_input_option: str = 'RAW'):
        credentials = self.authenticate()
        cell_range = self.calculate_cell_range_by_data(SheetsCell(start_cell), data)
        service = build('sheets', 'v4', credentials=credentials)
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            valueInputOption=value_input_option,
            range=f'{sheet_name}!{cell_range}',
            body=dict(majorDimension='ROWS', values=data),
        ).execute()

    def recalculate_formula(self, spreadsheet_id: str, sheet_name: str, cell: str):
        cell_data = self.read_data_from_sheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name, sheetrange=cell,
                                              value_render_option='FORMULA')
        formula = cell_data[0][0]

        self.write_data_to_sheet(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name, start_cell=cell, data=[[formula]],
                                 value_input_option='USER_ENTERED')

    def read_celldata_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)
        result = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            ranges=[sheet_name + '!' + sheetrange], includeGridData=True
        ).execute()
        return result['sheets'][0]['data'][0]

    def read_data_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str,
                             return_raw_results: bool = False, value_render_option: str ='FORMATTED_VALUE'):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, valueRenderOption=value_render_option,
            range=sheet_name + '!' + sheetrange
        ).execute()
        if return_raw_results:
            return result
        else:
            return result.get('values', [])

    def clear_cells_within_range(self, spreadsheet_id: str, sheet_name: str, sheetrange: str):
        credentials = self.authenticate()

        dimensions = self._get_range_dimensions(sheetrange)
        rows = dimensions[0]
        columns = dimensions[1]
        row = [''] * columns
        data = [row] * rows

        service = build('sheets', 'v4', credentials=credentials)
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            valueInputOption='RAW',
            range=sheet_name + '!' + sheetrange,
            body=dict(
                majorDimension='ROWS',
                values=data)
        ).execute()

    def find_first_nonempty_row_from_starting_cell(self, spreadsheet_id, sheet_name, start_cell, max_rows:int = 10):
        start_sheetscell = SheetsCell(start_cell)
        column_cell_content = []
        while column_cell_content == [] and start_sheetscell.row < max_rows:
            column_cell_content = self.read_data_from_sheet(spreadsheet_id, sheet_name, start_sheetscell.cell + ':' + start_sheetscell.cell)
            start_sheetscell.update_row_by_adding_number(1)
        if column_cell_content == []:
            return start_sheetscell.row
        return start_sheetscell.row

    # use max row and limit by step size, to grow exp
    def find_first_empty_row_from_starting_cell(self, spreadsheet_id: str, sheet_name: str, start_cell: str,
                                                step_factor: int = 4, step_start: int = 1000) -> int:
        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id=spreadsheet_id)
        grid_props = sheets[sheet_name]['gridProperties']
        max_row = grid_props['rowCount']

        start_sheetscell = SheetsCell(start_cell)
        total_nonempty_rows = 0
        step_size = step_start

        if max_row <= step_start:
            end_sheetscell = start_sheetscell.copy()
            end_sheetscell.row = max_row
            data = self.read_data_from_sheet(spreadsheet_id, sheet_name, start_sheetscell.cell + ':' + end_sheetscell.cell)
            nonempty_rows = self._number_of_nonempty_rows_in_data(data)
            return start_sheetscell.row + nonempty_rows

        end_sheetscell = start_sheetscell.copy()
        end_sheetscell.update_row_by_adding_number(step_size)
        while True:
            if end_sheetscell.row > max_row:
                end_sheetscell.row = max_row
            data = self.read_data_from_sheet(spreadsheet_id, sheet_name, start_sheetscell.cell + ':' + end_sheetscell.cell)
            nonempty_rows = self._number_of_nonempty_rows_in_data(data)
            total_nonempty_rows += nonempty_rows
            if nonempty_rows == 0 or end_sheetscell.row >= max_row:
                break
            start_sheetscell.update_row_by_adding_number(step_size + 1)
            step_size += step_size * step_factor
            end_sheetscell.update_row_by_adding_number(step_size)

        start_sheetscell = SheetsCell(start_cell)
        start_sheetscell.update_row_by_adding_number(total_nonempty_rows)
        return start_sheetscell.row

    def _number_of_nonempty_rows_in_data(self, data: list) -> int:
        if len(data) == 0 or len(data[0]) == 0:
            return 0
        for i, row in enumerate(data):
            if row[0] == '':
                return i
        return len(data)

    def authenticate(self) -> Credentials:
        if self.credentials is not None:
            return self.credentials

        cred_file_path = Path(self.service_cred_path)
        if not cred_file_path.is_file():
            raise FileNotFoundError(f"could not find the credentials file at {cred_file_path}")

        with open(cred_file_path) as cred_file:
            gcp_sa_credentials = json.load(cred_file)

        self.credentials = service_account.Credentials.from_service_account_info(gcp_sa_credentials)
        return self.credentials

    def calculate_cell_range_by_data(self, cell_start: SheetsCell, data: list = None):
        if cell_start is None:
            raise ValueError("start_cell can't be empty")

        if len(data) == 0:
            raise ValueError("data can't be empty")

        cell_end = cell_start.copy()

        max_cells_in_row = max(map(lambda x: len(x), data))
        cell_end.update_column_by_adding_number(max_cells_in_row - 1)
        cell_end.update_row_by_adding_number(len(data) - 1)

        return cell_start.cell + ':' + cell_end.cell

    def _get_range_dimensions(self, sheetrange: str = ''):
        if ':' not in sheetrange:
            raise ValueError(f'{sheetrange} is not a valid range')
        cells = sheetrange.split(':')
        if len(cells) != 2:
            raise ValueError(f'{sheetrange} is not a valid range')
        try:
            startcell = SheetsCell(cells[0])
            endcell = SheetsCell(cells[1])
            rows = endcell._row - startcell._row + 1
            columns = endcell._column_int - startcell._column_int + 1
            return [rows, columns]
        except:
            raise ValueError(f'{sheetrange} is not a valid range')

    def automatic_resize_columns(self, spreadsheet_id: str = '', sheet_name: str = '', number_of_columns: int = 1):

        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{'autoResizeDimensions': {
                "dimensions": {
                    "sheetId": sheets[sheet_name]['sheetId'],
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": number_of_columns
                }
            }}])).execute()

    def write_formulae_cells(self, spreadsheet_id: str = '', sheet_name: str = '', start_cell: str = '', formulae: list = None):
        if len(formulae) == 0:
            return

        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        start = SheetsCell(start_cell)
        end = start.copy()
        end.update_row_by_adding_number(len(formulae) - 1)

        sheet_values = []
        for formula in formulae:
            sheet_values.append({
                "values": {
                    "userEnteredValue": {
                        "formulaValue": formula}}})

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{'updateCells': {
                "fields": 'userEnteredValue.formulaValue',
                "start": {
                    "sheetId": sheets[sheet_name]['sheetId'],
                    "rowIndex": start.row - 1,
                    "columnIndex": start._column_int - 1
                },
                "rows": [sheet_values]
            }}])).execute()

    def add_hyperlink_column(self, spreadsheet_id: str = '', sheet_name: str = '', start_cell: str = '',
                             link_type: str = 'awvinfra', column_data: list = None):
        if len(column_data) == 0:
            return

        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        start = SheetsCell(start_cell)
        end = start.copy()
        end.update_row_by_adding_number(len(column_data) - 1)

        sheet_values = []
        for row in column_data:
            if row is not None and row != '':
                url = ''
                if link_type == 'awvinfra':
                    url = f'https://apps.mow.vlaanderen.be/awvinfra/ui/#/?asset={row}'
                elif link_type == 'eminfra':
                    url = f'https://apps.mow.vlaanderen.be/eminfra/installaties/{row}'
                sheet_values.append({
                    "values": {
                        "userEnteredValue": {
                            "formulaValue": f'=HYPERLINK("{url}"; "{row}")'}}})
            else:
                sheet_values.append({
                    "values": {
                        "userEnteredValue": None}})

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{'updateCells': {
                "fields": 'userEnteredValue.formulaValue',
                "start": {
                    "sheetId": sheets[sheet_name]['sheetId'],
                    "rowIndex": start.row - 1,
                    "columnIndex": start._column_int - 1
                },
                "rows": [sheet_values]
            }}])).execute()

    def insert_empty_rows(self, spreadsheet_id, sheet_name, start_cell, number_of_rows: int):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        startsheetscell = SheetsCell(start_cell)

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{
                "insertDimension": {
                    "range": {
                        "sheetId": sheets[sheet_name]['sheetId'],
                        "dimension": "ROWS",
                        "startIndex": startsheetscell.row - 1,
                        "endIndex": startsheetscell.row + number_of_rows - 1
                    },
                    "inheritFromBefore": False
                }
            }])).execute()

    def freeze_top_rows(self, spreadsheet_id, sheet_name, rows: int):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheets[sheet_name]['sheetId'],
                        "gridProperties": {
                            "frozenRowCount": rows
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }])).execute()

    def rename_sheet(self, spreadsheet_id, sheet_name, new_sheet_name):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)

        sheets = self.get_sheets_in_spreadsheet(spreadsheet_id)
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=dict(requests=[{
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheets[sheet_name]['sheetId'],
                        "title": new_sheet_name
                    },
                    "fields": "title"
                }
            }])).execute()


class SingleSheetsWrapper:
    sheets_wrapper: SheetsWrapper | bool = None

    @classmethod
    def init(cls, service_cred_path: str = '', readonly_scope: None | bool = None):
        cls.sheets_wrapper = SheetsWrapper(service_cred_path, readonly_scope)

    @classmethod
    def get_wrapper(cls) -> SheetsWrapper:
        if cls.sheets_wrapper is None:
            raise RuntimeError('Run the init method of this class first')
        return cls.sheets_wrapper
