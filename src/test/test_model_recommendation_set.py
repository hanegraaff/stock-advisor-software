"""Author: Mark Hanegraaff -- 2020
    Testing class for the model.recommendation_set module
"""
import unittest
from datetime import datetime, date, timezone, timedelta
import botocore
from unittest.mock import patch
from exception.exceptions import ValidationError, AWSError
from model.recommendation_set import SecurityRecommendationSet
from connectors import aws_service_wrapper


class TestSecurityRecommendationSet(unittest.TestCase):
    """
        Testing class for the model.recommendation_set module
    """

    '''
        Exception/Validation testing
    '''

    def test_invalid_parameters(self):
        '''
            Combine these into a single test for brevity
        '''

        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(None, date.today(), date.today(
            ), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), None, date.today(
            ), date.today(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(
            ), None, datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(
            ), date.today(), None, 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(
            ), date.today(), date.today(), None, 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(
            ), date.today(), date.today(), 'STRATEGY_NAME', None, {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(
            ), date.today(), date.today(), 'STRATEGY_NAME', 'US Equities', None)
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), date.today(), date.today(
            ), date.today(), 'STRATEGY_NAME', 'US Equities', "Not A Dictionary")

    def test_valid_parameters(self):
        SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
        ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})

    def test_valid_dict(self):
        recommendation_set_dict = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-09-01T04:56:57.612693+00:00",
            "valid_from": "2019-08-01",
            "valid_to": "2019-08-31",
            "price_date": "2019-09-01",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities",
            "securities_set": [{
                "ticker_symbol": "GE",
                "price": 123.45
            }, {
                "ticker_symbol": "INTC",
                "price": 123.45
            }, {
                "ticker_symbol": "AAPL",
                "price": 123.45
            }]
        }

        SecurityRecommendationSet.from_dict(recommendation_set_dict)

    def test_invalid_dict_1(self):
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_dict({
                'x': 'y'
            })

    def test_invalid_dict_2(self):
        recommendation_set_dict = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-09-01T04:56:57.612693+00:00",
            "valid_from": "2019-08-01",
            "price_date": "2019-09-01",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities"
        }

        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_dict(recommendation_set_dict)

    def test_is_current_future_date(self):

        # Create a recommendation set from the past (2019/8)
        recommendation_set = SecurityRecommendationSet.from_parameters(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc),
            date(2019, 8, 1),
            date(2019, 8, 31),
            date(2019, 8, 31),
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        self.assertFalse(recommendation_set.is_current(
            date(2019, 9, 1)))

    def test_is_current_past_date(self):

        # Create a recommendation set from the past (2019/8)
        recommendation_set = SecurityRecommendationSet.from_parameters(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc),
            date(2019, 8, 1),
            date(2019, 8, 31),
            date(2019, 8, 31),
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        self.assertFalse(recommendation_set.is_current(
            date(2019, 7, 30)))

    def test_is_current_current_date(self):

        # Create a recommendation set from the past (2019/8)
        recommendation_set = SecurityRecommendationSet.from_parameters(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc),
            date(2019, 8, 1),
            date(2019, 8, 31),
            date(2019, 8, 31),
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        self.assertTrue(recommendation_set.is_current(
            date(2019, 8, 15)))

    def test_is_current_current_date_single(self):
        # Create a recommendation set from the past (2019/8)
        recommendation_set = SecurityRecommendationSet.from_parameters(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc),
            date(2019, 8, 1),
            date(2019, 8, 1),
            date(2019, 8, 1),
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        self.assertTrue(recommendation_set.is_current(
            date(2019, 8, 1)))
