import unittest
from connectors import intrinio_util
from exception.exceptions import ValidationError


class TestConnectorsIntrinioUtil(unittest.TestCase):

    '''
        get_year_date_range tests
    '''

    def test_year_range_valid_date(self):
        (date_from, date_to) = intrinio_util.get_year_date_range(2018, 0)

        self.assertEqual(date_from, "2018-01-01")
        self.assertEqual(date_to, "2018-12-31")

    def test_year_range_valid_date_extended(self):
        (date_from, date_to) = intrinio_util.get_year_date_range(2018, 10)

        self.assertEqual(date_from, "2018-01-01")
        self.assertEqual(date_to, "2019-01-10")

    def test_year_range_invaid_date(self):
        with self.assertRaises(ValidationError):
            intrinio_util.get_year_date_range(0, 0)

    def test_year_range_invalid_extendedby(self):
        with self.assertRaises(ValidationError):
            intrinio_util.get_year_date_range(2018, -1)

        with self.assertRaises(ValidationError):
            intrinio_util.get_year_date_range(2018, 360)

    '''
        get_month_date_range tests
    '''

    def test_month_range_valid_date(self):
        (date_from, date_to) = intrinio_util.get_month_date_range_str(2018, 1)

        self.assertEqual(date_from, "2018-01-01")
        self.assertEqual(date_to, "2018-01-31")

        (date_from, date_to) = intrinio_util.get_month_date_range_str(2018, 12)

        self.assertEqual(date_from, "2018-12-01")
        self.assertEqual(date_to, "2018-12-31")

    def test_month_range_invaid_year(self):
        with self.assertRaises(ValidationError):
            intrinio_util.get_month_date_range(0, 2)

    def test_month_range_invaid_month(self):
        with self.assertRaises(ValidationError):
            intrinio_util.get_month_date_range(2019, 13)

        with self.assertRaises(ValidationError):
            intrinio_util.get_month_date_range(2019, 0)

        with self.assertRaises(ValidationError):
            intrinio_util.get_month_date_range(2019, -1)
