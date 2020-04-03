import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from exception.exceptions import ValidationError
from model.recommendation_set import SecurityRecommendationSet

class TestSecurityRecommendationSet(unittest.TestCase):
    '''
        Exception/Validation testing
    '''

    def test_invalid_parameters(self):

        '''
            Combine these into a single test for brevity
        '''

        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(None, datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), None, datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), None, datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), None, 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), None, 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', None, {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', None)
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', "Not A Dictionary")

    def test_valid_parameters(self):
        SecurityRecommendationSet(datetime.now(), datetime.now(), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})

    def test_invalid_dict(self):
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_dict({
                'x' : 'y'
            })

    def test_valid_dict(self):
        d = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-03-01T04:56:57.612693+00:00",
            "analysis_start_date": "2019-08-01T00:00:00",
            "analysis_end_date": "2019-08-31T00:00:00",
            "price_date": "2019-09-01T02:34:12.876012+00:00",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities",
            "security_set": {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        }

        s = SecurityRecommendationSet.from_dict(d)

        self.assertEqual(s.set_id, d['set_id'])
        self.assertEqual(s.creation_date.year, 2020)
        self.assertEqual(s.creation_date.month, 3)
        self.assertEqual(s.creation_date.day, 1)
        self.assertEqual(s.creation_date.hour, 4)
        self.assertEqual(s.creation_date.minute, 56)
        self.assertEqual(s.creation_date.second, 57)

        self.assertEqual(s.analysis_start_date.year, 2019)
        self.assertEqual(s.analysis_start_date.month, 8)
        self.assertEqual(s.analysis_start_date.day, 1)
        self.assertEqual(s.analysis_start_date.hour, 0)
        self.assertEqual(s.analysis_start_date.minute, 0)
        self.assertEqual(s.analysis_start_date.second, 0)

        self.assertEqual(s.analysis_end_date.year, 2019)
        self.assertEqual(s.analysis_end_date.month, 8)
        self.assertEqual(s.analysis_end_date.day, 31)
        self.assertEqual(s.analysis_end_date.hour, 0)
        self.assertEqual(s.analysis_end_date.minute, 0)
        self.assertEqual(s.analysis_end_date.second, 0)

        self.assertEqual(s.price_date.year, 2019)
        self.assertEqual(s.price_date.month, 9)
        self.assertEqual(s.price_date.day, 1)
        self.assertEqual(s.price_date.hour, 2)
        self.assertEqual(s.price_date.minute, 34)
        self.assertEqual(s.price_date.second, 12)

        self.assertEqual(s.strategy_name, d['strategy_name'])
        self.assertEqual(s.security_type, d['security_type'])
        self.assertDictEqual(s.security_set, {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            })

    def test_valid_analysis_date_yyyy_mm_dd(self):
        d = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-03-01T04:56:57.612693+00:00",
            "analysis_start_date": "2019-08-01",
            "analysis_end_date": "2019-08-31",
            "price_date": "2019-09-01T02:34:12.876012+00:00",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities",
            "security_set": {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        }

        s = SecurityRecommendationSet.from_dict(d)

        self.assertEqual(s.analysis_start_date.year, 2019)
        self.assertEqual(s.analysis_start_date.month, 8)
        self.assertEqual(s.analysis_start_date.day, 1)
        self.assertEqual(s.analysis_start_date.hour, 0)
        self.assertEqual(s.analysis_start_date.minute, 0)
        self.assertEqual(s.analysis_start_date.second, 0)

        self.assertEqual(s.analysis_end_date.year, 2019)
        self.assertEqual(s.analysis_end_date.month, 8)
        self.assertEqual(s.analysis_end_date.day, 31)
        self.assertEqual(s.analysis_end_date.hour, 0)
        self.assertEqual(s.analysis_end_date.minute, 0)
        self.assertEqual(s.analysis_end_date.second, 0)

        # now test that data date can be converted back to string
        d = s.to_dict()
        self.assertEqual(d['analysis_start_date'], "2019-08-01T00:00:00")
        self.assertEqual(d['analysis_end_date'], "2019-08-31T00:00:00")


    def test_valid_dictionary(self):
        p = SecurityRecommendationSet(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc), 
            datetime(2019, 8, 1, 0, 0, 0), 
            datetime(2019, 8, 31, 0, 0, 0), 
            datetime(2019, 9, 1, 2, 34, 12, tzinfo=timezone.utc), 
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        p.set_id = "xxx"
        self.assertDictEqual(p.to_dict(), {
            "set_id": "xxx",
            "creation_date": "2020-03-01T04:56:57+00:00",
            "analysis_start_date": "2019-08-01T00:00:00",
            "analysis_end_date": "2019-08-31T00:00:00",
            "price_date": "2019-09-01T02:34:12+00:00",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities",
            "security_set": {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        })

