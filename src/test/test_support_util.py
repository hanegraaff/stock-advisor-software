import unittest
from exception.exceptions import ValidationError
from support import util


class TestSupportUtil(unittest.TestCase):

    def test_date_to_iso_string_with_error(self):
        with self.assertRaises(ValidationError):
            util.date_to_iso_string("not a date")

    def test_date_to_iso_string_none(self):
        self.assertEqual(util.date_to_iso_string(None), "None")

    def test_date_to_iso_utc_string_with_error(self):
        with self.assertRaises(ValidationError):
            util.date_to_iso_utc_string("not a date")

    def test_date_to_iso_utc_string_none(self):
        self.assertEqual(util.date_to_iso_utc_string(None), "None")
