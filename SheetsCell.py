import copy
import re


class SheetsCell:
    def __init__(self, cell: str = ''):
        if cell == '':
            raise ValueError("can't initialize a SheetsCell object without input")

        self._column_str = ''
        self._column_int = -1
        self._row = ''

        self.cell = cell

    @property
    def row(self):
        return int(self._row)

    @row.setter
    def row(self, value: int):
        self._row = value

    @property
    def cell(self):
        return self._column_str + str(self._row)

    @cell.setter
    def cell(self, value):
        try:
            self._column_str = re.split(r'\d', value)[0]
            self._row = int(value[len(self._column_str):])
            self._column_int = self._convert_column_to_number(self._column_str)

        except ValueError as ex:
            raise ex
        except:
            raise ValueError(f"can't set or update SheetsCell object with input {value}")

    @staticmethod
    def _convert_column_to_number(column: str) -> int:
        if len(column) < 1 or len(column) > 3:
            raise ValueError('the max value of the column is ZZZ')

        sum = 0
        for i, letter in enumerate(column[::-1]):
            sum += (ord(letter) - 64) * (26 ** i)

        return sum

    @staticmethod
    def _convert_number_to_column(number: int) -> str:
        if number < 1 or number > 18278:
            raise ValueError

        first = (number - 1) % 26 + 1
        if number < 27:
            return chr(ord('@') + first)

        second = (int((number - 1) / 26) - 1) % 26 + 1
        if number < 703:
            return chr(ord('@') + second) + chr(ord('@') + first)

        third = (int((number - 27) / 676) - 1) % 26 + 1
        return chr(ord('@') + third) + chr(ord('@') + second) + chr(ord('@') + first)

    def copy(self):
        return copy.copy(self)

    def update_row_by_adding_number(self, row_update: int):
        self._row += row_update

    def update_column_by_adding_number(self, column_update: int):
        self._column_int += column_update
        self._column_str = self._convert_number_to_column(self._column_int)
