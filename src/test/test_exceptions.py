"""Author: Mark Hanegraaff -- 2020
    Testing class for the exception.exceptions module
"""
import unittest
from exception.exceptions import ValidationError, CalculationError, DataError, ReportError, AWSError, TradeError
from requests import Response


class TestExceptions(unittest.TestCase):
    """Author: Mark Hanegraaff -- 2020
        Testing class for the exception.exceptions module
    """

    def test_simple_exception_nocause(self):

        self.assertEqual(str(ValidationError("Cannot do XYZ", None)),
                         "Validation Error: Cannot do XYZ")
        self.assertEqual(str(CalculationError("Cannot do XYZ", None)),
                         "Calculation Error: Cannot do XYZ")
        self.assertEqual(str(DataError("Cannot do XYZ", None)),
                         "Data Error: Cannot do XYZ")
        self.assertEqual(str(ReportError("Cannot do XYZ", None)),
                         "Report Error: Cannot do XYZ")
        self.assertEqual(repr(AWSError("Cannot do XYZ", None)),
                         "AWS Error: Cannot do XYZ")

    '''
        ValidationError Tests (covers all exceptions)
    '''

    def test_simple_exception_with_exceptioncause(self):

        empty_dict = {}

        try:
            empty_dict['XXX']
            self.fail("Error in test setup")
        except KeyError as ke:
            validation_error = ValidationError("Cannot do XYZ", ke)
            self.assertEqual(
                str(validation_error), "Validation Error: Cannot do XYZ. Caused by: 'XXX'")

    def test_simple_exception_with_stringcause(self):

        validation_error = ValidationError("Cannot do XYZ", "Some Error")

        self.assertEqual(
            str(validation_error), "Validation Error: Cannot do XYZ. Caused by: Some Error")

    def test_simple_exception_with_numbercause(self):

        validation_error = ValidationError("Cannot do XYZ", 3.2)

        self.assertEqual(
            str(validation_error), "Validation Error: Cannot do XYZ. Caused by: 3.2")

    def test_simple_exception_with_chainedcause(self):

        root_cause = Exception("Root Cause")
        chained_cause = Exception("Some reason", root_cause)

        validation_error = ValidationError("Cannot do XYZ", chained_cause)

        # mac os and linux produce slightly different results
        self.assertTrue(
            "Validation Error: Cannot do XYZ. Caused by: ('Some reason', Exception('Root Cause" in str(validation_error))

    '''
        AWS Tests
    '''

    def test_aws_error(self):

        aws_exception = Exception("Some AWS Error")

        aws = AWSError("Cannot do XYZ", aws_exception)

        # mac os and linux produce slightly different results
        self.assertFalse(aws.resource_not_found())

    def test_aws_resource_not_found(self):

        aws_exception = Exception(
            "An error occurred (404) when calling the HeadObject operation: Not Found")

        aws = AWSError("Cannot do XYZ", aws_exception)

        # mac os and linux produce slightly different results
        self.assertTrue(aws.resource_not_found())

    '''
        TradeErrors
    '''

    def test_trade_error_with_api_response(self):

        response = Response()
        response.reason = "Server Error"
        response.status_code = 500

        trade_error = TradeError("Some Error", None, response)

        self.assertEqual(str(trade_error),
                         "Trade Error (500) [Server Error]: Some Error")

    def test_trade_error_without_api_response(self):

        trade_error = TradeError("Some Error", None, None)

        self.assertEqual(str(trade_error), "Trade Error: Some Error")
