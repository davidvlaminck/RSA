import json
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

        if readonly_scope is None:
            raise ValueError('set readonly_scope to True or False')

    def write_data_to_sheet(self, spreadsheet_id: str, sheet_name: str, start_cell: str, data: list):
        credentials = self.authenticate()
        cell_range = self.calculate_cell_range_by_data(SheetsCell(start_cell), data)
        service = build('sheets', 'v4', credentials=credentials)
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            valueInputOption='RAW',
            range=sheet_name + '!' + cell_range,
            body=dict(
                majorDimension='ROWS',
                values=data)
        ).execute()

    def read_data_from_sheet(self, spreadsheet_id: str, sheet_name: str, sheetrange: str):
        credentials = self.authenticate()
        service = build('sheets', 'v4', credentials=credentials)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name + '!' + sheetrange).execute()
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

    def find_first_empty_row_from_starting_cell(self, spreadsheet_id: str, sheet_name: str, start_cell: str, step_size: int = 1000) -> str:
        start_sheetscell = SheetsCell(start_cell)
        total_nonempty_rows = 0

        while True:
            end_sheetscell = start_sheetscell.copy()
            end_sheetscell.update_row_by_adding_number(step_size - 1)
            data = self.read_data_from_sheet(spreadsheet_id, sheet_name, start_sheetscell.cell + ':' + end_sheetscell.cell)
            nonempty_rows = self._number_of_nonempty_rows_in_data(data)
            total_nonempty_rows += nonempty_rows
            if nonempty_rows == 0:
                break
            start_sheetscell.update_row_by_adding_number(step_size)
            end_sheetscell.update_row_by_adding_number(step_size)

        start_sheetscell = SheetsCell(start_cell)
        start_sheetscell.update_row_by_adding_number(total_nonempty_rows)
        return start_sheetscell.cell


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


