import csv
import tempfile
import unittest
from pathlib import Path
from calculate import aggregate, FIELDS


class AggregationTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'sales.csv'
            with path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(FIELDS)
                writer.writerows(rows)
            return aggregate(path)

    def test_duplicates_statuses_missing_cancelled_quantity_and_sort(self):
        a = ['1', '2026-09-02', 'B', '2', '10.25', 'Delivered ']
        rows = [a, a, ['2', '2026-09-02', 'B', '', '10', 'canceled'],
                ['3', '2026-09-02', 'A', '1', '5', 'CANCELLED'],
                ['4', '2026-09-01', 'B', '1', '0.10', 'DELIVERED'],
                ['5', '2026-09-02', 'B', '1', '0.20', 'delivered']]
        self.assertEqual(self.run_rows(rows), [
            ('A', '2026-09-02', 1, '0.00'),
            ('B', '2026-09-01', 1, '0.10'),
            ('B', '2026-09-02', 3, '20.70')])

    def test_conflicting_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            self.run_rows([['1', '2026-09-01', 'A', '1', '10', s]
                           for s in ['delivered', 'cancelled']])

    def test_invalid_data_is_rejected(self):
        for column, value in [(0, ''), (1, '2026-02-30'), (2, ''),
                              (3, ''), (3, '-1'), (4, 'NaN'),
                              (4, '-10'), (4, '1.234'), (5, 'unknown')]:
            row = ['1', '2026-09-01', 'A', '1', '10', 'delivered']
            row[column] = value
            with self.subTest(column=column, value=value):
                with self.assertRaises(ValueError):
                    self.run_rows([row])

    def test_empty_input(self):
        self.assertEqual(self.run_rows([]), [])


if __name__ == '__main__':
    unittest.main()
