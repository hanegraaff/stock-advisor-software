import unittest
from unittest.mock import patch
from datetime import datetime
from exception.exceptions import ValidationError, AWSError
from services import recommendation_svc
from connectors import aws_service_wrapper
from model.recommendation_set import SecurityRecommendationSet
from support import constants


class TestServicesRecommendation(unittest.TestCase):

    '''
        validate_environment tests
    '''

    def test_validate_environment_valid(self):
        self.assertEqual(
            recommendation_svc.validate_environment('test'), 'TEST')
        self.assertEqual(
            recommendation_svc.validate_environment('tEsT'), 'TEST')
        self.assertEqual(recommendation_svc.validate_environment(
            'production'), 'PRODUCTION')
        self.assertEqual(recommendation_svc.validate_environment(
            'pRodUCTION'), 'PRODUCTION')

    def test_validate_environment_invalid(self):
        with self.assertRaises(ValidationError):
            recommendation_svc.validate_environment('invalid')
    '''
        validate_price_date tests
    '''

    def test_validate_price_date_invalid_date(self):
        with self.assertRaises(ValidationError):
            recommendation_svc.validate_price_date("invalid date format")

    '''
        validate_commandline_parameters tests
    '''

    def test_validate_commandline_parameters_valid(self):
        current_price = datetime(2020, 3, 1)

        recommendation_svc.validate_commandline_parameters(
            2020, 2, current_price)

    def test_validate_commandline_parameters_future_price_date(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(
                2020, 3, current_price)

    def test_validate_commandline_parameters_invalid_year(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(
                1900, 3, current_price)

    def test_validate_commandline_parameters_invalid_month(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(
                2020, 100, current_price)

    '''
        compute_analysis_period tests
    '''

    def test_compute_analysis_period(self):
        current_price = datetime(2020, 3, 1)
        (year, month) = recommendation_svc.compute_analysis_period(current_price)

        self.assertEqual(year, 2020)
        self.assertEqual(month, 2)

    '''
        sns publishing tests
    '''
    def test_notify_new_recommendation_with_boto_error(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value',
                        return_value="some_sns_arn"), \
            patch.object(aws_service_wrapper, 'sns_publish_notification',
                        side_effect=AWSError("test exception", None)):

            with self.assertRaises(AWSError):
                s = SecurityRecommendationSet.from_parameters(datetime.now(), datetime.now(
                ), datetime.now(), datetime.now(), 'STRATEGY_NAME', 'US Equities', {'AAPL': 100})

                recommendation_svc.notify_new_recommendation(s, 'sa')


    def test_notify_notify_error_boto_error(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value',
                        return_value="some_sns_arn"), \
            patch.object(aws_service_wrapper, 'sns_publish_notification',
                        side_effect=AWSError("test exception", None)):

            with self.assertRaises(AWSError):
                recommendation_svc.notify_error(Exception("None"), 'stack trace', 'sa')
