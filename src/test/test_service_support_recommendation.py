import unittest
from unittest.mock import patch
from datetime import datetime
from exception.exceptions import ValidationError, FileSystemError, AWSError
from service_support import recommendation_svc
from cloud import aws_service_wrapper
from support import constants

class TestServiceSupportRecommendation(unittest.TestCase):
    
    '''
        from_yyyymmdd tests
    '''

    def test_from_yyyymmdd_invalid_date(self):
        with self.assertRaises(ValidationError):
            recommendation_svc.from_yyyymmdd("invalid date format")
        
    '''
        validate_commandline_parameters tests
    '''

    def test_validate_commandline_parameters_valid(self):
        current_price = datetime(2020, 3, 1)

        recommendation_svc.validate_commandline_parameters(2020, 2, current_price)

    def test_validate_commandline_parameters_future_price_date(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(2020, 3, current_price)

    def test_validate_commandline_parameters_invalid_year(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(1900, 3, current_price)
         
    def test_validate_commandline_parameters_invalid_month(self):
        current_price = datetime(2020, 3, 1)

        with self.assertRaises(ValidationError):
            recommendation_svc.validate_commandline_parameters(2020, 100, current_price)
               
    '''
        compute_analysis_period tests
    '''
    
    def test_compute_analysis_period(self):
        current_price = datetime(2020, 3, 1)
        (year, month) = recommendation_svc.compute_analysis_period(current_price)

        self.assertEqual(year, 2020)
        self.assertEqual(month, 2)

