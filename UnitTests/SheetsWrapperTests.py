import unittest

from outputs.sheets_cell import SheetsCell
from outputs.sheets_wrapper import SheetsWrapper


class SheetsWrapperTests(unittest.TestCase):
    def test_calculate_cell_range_no_cell_or_no_data(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
        with self.assertRaises(ValueError):
            sheetsWrapper.calculate_cell_range_by_data(SheetsCell(''), [['']])
        with self.assertRaises(ValueError):
            sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [])

    def test_calculate_cell_range_A1_1_cell(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [['']])
        self.assertEqual('A1:A1', cell_range)

    def test_calculate_cell_range_A1_2_cells_in_1_row(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [['', '']])
        self.assertEqual('A1:B1', cell_range)

    def test_calculate_cell_range_A1_2_cells_in_1_column(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        cell_range = sheetsWrapper.calculate_cell_range_by_data(SheetsCell('A1'), [[''], ['']])
        self.assertEqual('A1:A2', cell_range)

    def test_number_of_nonempty_rows_in_data_empty_data(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([])
        self.assertEqual(0, number_of_rows)
        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([[]])
        self.assertEqual(0, number_of_rows)
        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['']])
        self.assertEqual(0, number_of_rows)

    def test_number_of_nonempty_rows_in_data_1_row(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['']])
        self.assertEqual(1, number_of_rows)
        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a']])
        self.assertEqual(1, number_of_rows)

    def test_number_of_nonempty_rows_in_data_2_rows(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)

        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['a'], ['']])
        self.assertEqual(2, number_of_rows)
        number_of_rows = sheetsWrapper._number_of_nonempty_rows_in_data([['a'], ['a']])
        self.assertEqual(2, number_of_rows)

    def test_get_range_dimensions_invalid_ranges(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
        with self.assertRaises(ValueError):
            sheetsWrapper._get_range_dimensions('')
        with self.assertRaises(ValueError):
            sheetsWrapper._get_range_dimensions('A:A:A')
        with self.assertRaises(ValueError):
            sheetsWrapper._get_range_dimensions('A1:2')

    def test_get_range_dimensions_valid_ranges(self):
        sheetsWrapper = SheetsWrapper(service_cred_path='a', readonly_scope=False)
        dims = sheetsWrapper._get_range_dimensions('A1:A1')
        self.assertEqual(1, dims[0])
        self.assertEqual(1, dims[1])

        dims = sheetsWrapper._get_range_dimensions('A1:C2')
        self.assertEqual(2, dims[0])
        self.assertEqual(3, dims[1])

