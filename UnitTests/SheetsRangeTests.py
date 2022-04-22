import unittest

from SheetsCell import SheetsCell


class SheetsRangeTests(unittest.TestCase):
    def test_init_SheetsRange(self):
        range1 = SheetsCell('A1')
        self.assertEqual('A1', range1.cell)
        self.assertEqual('A', range1._column_str)
        self.assertEqual(1, range1._column_int)
        self.assertEqual(1, range1._row)

    def test_update_SheetsRange(self):
        range1 = SheetsCell('A1')
        range1.update_row_by_adding_number(1)
        self.assertEqual('A2', range1.cell)
        range1.update_column_by_adding_number(1)
        self.assertEqual('B2', range1.cell)

    def test_create_second_SheetsRange(self):
        range1 = SheetsCell('A1')
        range2 = range1.copy()
        range2.cell = 'B2'
        self.assertEqual('B2', range2.cell)
        self.assertEqual('A1', range1.cell)

    def test_convert_number_to_column(self):
        testlist = [(1, 'A'),
                    (2, 'B'),
                    (26, 'Z'),
                    (27, 'AA'),
                    (28, 'AB'),
                    (53, 'BA'),
                    (702, 'ZZ'),
                    (703, 'AAA'),
                    (729, 'ABA'),
                    (18278, 'ZZZ')]

        for test in testlist:
            with self.subTest(f'{str(test[0])} to {test[1]}'):
                column = SheetsCell._convert_number_to_column(test[0])
                self.assertEqual(column, test[1])

        with self.subTest('invalid values'):
            with self.assertRaises(ValueError):
                SheetsCell._convert_number_to_column(18279)
            with self.assertRaises(ValueError):
                SheetsCell._convert_number_to_column(0)

    def test_convert_column_to_number(self):
        testlist = [(1, 'A'),
                    (2, 'B'),
                    (26, 'Z'),
                    (27, 'AA'),
                    (28, 'AB'),
                    (53, 'BA'),
                    (702, 'ZZ'),
                    (703, 'AAA'),
                    (729, 'ABA'),
                    (18278, 'ZZZ')]

        for test in testlist:
            with self.subTest(f'{str(test[1])} to {test[0]}'):
                column = SheetsCell._convert_column_to_number(test[1])
                self.assertEqual(column, test[0])

        with self.subTest('invalid values'):
            with self.assertRaises(ValueError):
                SheetsCell._convert_column_to_number('')
            with self.assertRaises(ValueError):
                SheetsCell._convert_column_to_number('AAAA')
