"""Author: Mark Hanegraaff -- 2020

Testing class for the connectors.intrinio_data module
"""

import unittest
import requests
from unittest.mock import patch, Mock
from intrinio_sdk.rest import ApiException
from exception.exceptions import ValidationError, DataError
from connectors import intrinio_data
from connectors import intrinio_util
from support.financial_cache import FinancialCache
import time
import datetime
from intrinio_sdk.rest import ApiException


class TestConnectorsIntrinioData(unittest.TestCase):

    """
        Testing class for the connectors.intrinio_data module
    """

    '''
        Decorator Tests
    '''

    RETRY_ERROR_COUNT = 5

    def test_retry_server_errors_no_exception(self):
        mock = Mock(return_value=None)
        test_function = intrinio_data.retry_server_errors(mock)
        test_function()

    def test_retry_server_errors_validtion_error(self):
        mock = Mock(side_effect=ValidationError("Mock Error", None))
        test_function = intrinio_data.retry_server_errors(mock)

        with self.assertRaises(ValidationError):
            test_function()

        self.assertEqual(mock.call_count, 1)

    def test_retry_server_errors_api_error_499(self):
        with patch.object(time, 'sleep', return_value=None):
            mock = Mock(side_effect=DataError(
                "Mock error", ApiException(499, "Mock Error")))
            test_function = intrinio_data.retry_server_errors(mock)

            with self.assertRaises(DataError):
                test_function()

            self.assertEqual(mock.call_count, 1)

    def test_retry_server_errors_api_error_500(self):
        with patch.object(time, 'sleep', return_value=None):
            mock = Mock(side_effect=DataError(
                "Mock error", ApiException(500, "Mock Error")))
            test_function = intrinio_data.retry_server_errors(mock)

            with self.assertRaises(DataError):
                test_function()

            self.assertEqual(mock.call_count, self.RETRY_ERROR_COUNT)

    def test_retry_server_errors_api_error_501(self):
        with patch.object(time, 'sleep', return_value=None):
            mock = Mock(side_effect=DataError(
                "Mock error", ApiException(501, "Mock Error")))
            test_function = intrinio_data.retry_server_errors(mock)

            with self.assertRaises(DataError):
                test_function()

            self.assertEqual(mock.call_count, self.RETRY_ERROR_COUNT)

    '''
        API Endpoint Test
    '''

    def test_test_api_endpoint_with_exception(self):
        with patch.object(requests, 'request',
                          side_effect=requests.ConnectionError("Connection Error")):
            with self.assertRaises(DataError):
                intrinio_data.test_api_endpoint()

    '''
        Company Data API test
    '''

    def test_read_financial_metric_with_api_exception(self):
        with patch.object(intrinio_data.COMPANY_API, 'get_company_historical_data',
                          side_effect=ApiException("Server Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            (start_date) = intrinio_util.get_year_date_range(2018, 0)[0]

            with self.assertRaises(DataError):
                intrinio_data._get_company_historical_data(
                    'NON-EXISTENT-TICKER', start_date, start_date, 'tag')

    def test_aggregate_by_year_month_1(self):

        input = [
            {'date': datetime.datetime(2019, 9, 1), 'value': 10},
            {'date': datetime.datetime(2019, 9, 15), 'value': 20},
            {'date': datetime.datetime(2019, 10, 12), 'value': 30}
        ]

        expected_out = {
            2019: {
                9: 15.0,
                10: 30.0
            }
        }

        self.assertDictEqual(
            expected_out, intrinio_data._aggregate_by_year_month(input))

    def test_aggregate_by_year_month_no_input(self):

        input = []
        expected_out = {}

        self.assertDictEqual(
            expected_out, intrinio_data._aggregate_by_year_month(input))

    def test_aggregate_by_year_month_null_input(self):

        input = None
        expected_out = {}

        self.assertDictEqual(
            expected_out, intrinio_data._aggregate_by_year_month(input))

    '''
        Data points test
    '''

    def test_read_company_data_point_with_api_exception(self):
        with patch.object(intrinio_data.COMPANY_API, 'get_company_data_point_number',
                          side_effect=ApiException("Server Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(DataError):
                intrinio_data._read_company_data_point(
                    'NON-EXISTENT-TICKER', 'tag')

    '''
        Financial statement tests
    '''

    def test_historical_cashflow_stmt_with_api_exception(self):
        with patch.object(intrinio_data.FUNDAMENTALS_API, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_cashflow_stmt(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    def test_historical_income_stmt_with_api_exception(self):
        with patch.object(intrinio_data.FUNDAMENTALS_API, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_income_stmt(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    def test_historical_balacesheet_stmt_with_api_exception(self):
        with patch.object(intrinio_data.FUNDAMENTALS_API, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_balance_sheet(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    '''
        Stock Price Tests
    '''

    def test_daily_stock_prices_with_api_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_stock_prices',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(DataError):
                intrinio_data.get_daily_stock_close_prices(
                    'NON-EXISTENT-TICKER', datetime.date(2018, 1, 1), datetime.date(2019, 1, 1))

    def test_daily_stock_prices_with_other_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_stock_prices',
                          side_effect=KeyError("xxx")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(ValidationError):
                intrinio_data.get_daily_stock_close_prices(
                    'NON-EXISTENT-TICKER', datetime.date(2018, 1, 1), datetime.date(2019, 1, 1))

    def test_latest_stock_prices_invalid_lookback(self):
        with self.assertRaises(ValidationError):
            intrinio_data.get_latest_close_price(
                'AAPL', datetime.date(2018, 1, 1), 25)

    def test_latest_stock_prices_with_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_stock_prices',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):
            with self.assertRaises(DataError):
                intrinio_data.get_latest_close_price(
                    'XXX', datetime.date(2018, 1, 1), 5)

    '''
        Stock Indicator Tests
    '''

    def test_get_macd_indicator_with_api_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_macd',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(DataError):
                intrinio_data.get_macd_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), 12, 26, 9)

    def test_get_macd_indicator_with_generic_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_macd',
                          side_effect=Exception("Some Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(ValidationError):
                intrinio_data.get_macd_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), 12, 26, 9)

    def test_get_macd_indicator_with_bad_parameters(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_macd',
                          side_effect=Exception("Some Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(ValidationError):
                intrinio_data.get_macd_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), -1, -1, -1)

    def test_get_sma_indicator_with_api_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_sma',
                          side_effect=ApiException("Not Found")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(DataError):
                intrinio_data.get_sma_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), 50)

    def test_get_sma_indicator_with_generic_exception(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_sma',
                          side_effect=Exception("Some Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(ValidationError):
                intrinio_data.get_sma_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), 50)

    def test_get_sma_indicator_with_bad_parameters(self):
        with patch.object(intrinio_data.SECURITY_API, 'get_security_price_technicals_sma',
                          side_effect=Exception("Some Error")), \
                patch.object(FinancialCache, 'read', return_value=None), \
                patch.object(FinancialCache, 'write', return_value=None):

            with self.assertRaises(ValidationError):
                intrinio_data.get_sma_indicator(
                    'AAPL', datetime.datetime(2020, 1, 1), datetime.datetime(2020, 5, 29), -1)
