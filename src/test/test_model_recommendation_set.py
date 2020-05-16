import unittest
from datetime import datetime, timezone, timedelta
import botocore
from unittest.mock import patch
from exception.exceptions import ValidationError, AWSError
from model.recommendation_set import SecurityRecommendationSet
from connectors import aws_service_wrapper


class TestSecurityRecommendationSet(unittest.TestCase):
    '''
        Exception/Validation testing
    '''

    def test_invalid_parameters(self):
        '''
            Combine these into a single test for brevity
        '''

        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(None, datetime.now(), datetime.now(
            ), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), None, datetime.now(
            ), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), None, datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), datetime.now(), None, 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), datetime.now(), datetime.now(), None, 'US Equities', {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), datetime.now(), datetime.now(), 'STRATEGY_NAME', None, {'AAPL': 100})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', None)
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
            ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {})
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(), datetime.now(
            ), datetime.now(), 'STRATEGY_NAME', 'US Equities', "Not A Dictionary")

    def test_valid_parameters(self):
        SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
        ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})

    def test_valid_dict(self):
        d = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-09-01T04:56:57.612693+00:00",
            "analysis_start_date": "2019-08-01T04:00:00+00:00",
            "analysis_end_date": "2019-08-31T04:00:00+00:00",
            "price_date": "2019-09-01T02:34:12.876012+00:00",
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

        SecurityRecommendationSet.from_dict(d)

    def test_invalid_dict_1(self):
        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_dict({
                'x': 'y'
            })

    def test_invalid_dict_2(self):
        d = {
            "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
            "creation_date": "2020-09-01T04:56:57.612693+00:00",
            "analysis_start_date": "2019-08-01T04:00:00+00:00",
            "price_date": "2019-09-01T02:34:12.876012+00:00",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities"
        }

        with self.assertRaises(ValidationError):
            SecurityRecommendationSet.from_dict(d)

    def test_is_current_false(self):
        '''
            Test that a recommendation set that is several months
            old is reported as not current
        '''

        # Create a recommendation set from the past (2019/8)
        p = SecurityRecommendationSet.from_parameters(
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

        self.assertFalse(p.is_current())

    def test_is_current_true(self):
        '''
            Test that a recommendation from last month
            relative to the current date is reported as current
        '''
        now = datetime.now()
        last = now - timedelta(days=1)

        analysis_date = datetime(now.year, last.month, 1, 0, 0, 0)

        # Create a recommendation set from the past (2019/8)
        p = SecurityRecommendationSet.from_parameters(
            datetime(2020, 3, 1, 4, 56, 57, tzinfo=timezone.utc),
            analysis_date,
            analysis_date,
            datetime(2019, 9, 1, 2, 34, 12, tzinfo=timezone.utc),
            "PRICE_DISPERSION",
            "US Equities",
            {
                "GE": 123.45,
                "INTC": 123.45,
                "AAPL": 123.45
            }
        )

        self.assertTrue(p.is_current())

    def test_send_sns_notification_with_boto_error(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value',
                          return_value="some_sns_arn"), \
            patch.object(aws_service_wrapper, 'sns_publish_notification',
                         side_effect=AWSError("test exception", None)):

            with self.assertRaises(AWSError):
                s = SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
                ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})

                s.send_sns_notification("sa")
