import unittest
from unittest.mock import patch
from intrinio_sdk.rest import ApiException
from exception.exceptions import ValidationError, DataError
from data_provider import intrinio_data
from data_provider import intrinio_util
from test import nop
import datetime


class TestDataProviderIntrinioData(unittest.TestCase):

    '''
        Company Data API test
    '''

    def test_read_financial_metric_with_api_exception(self):
        with patch.object(intrinio_data.company_api, 'get_company_historical_data',
                          side_effect=ApiException("Server Error")), \
                patch('support.financial_cache.cache', new=nop.Nop()):

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
        with patch.object(intrinio_data.company_api, 'get_company_data_point_number',
                          side_effect=ApiException("Server Error")), \
                patch('support.financial_cache.cache', new=nop.Nop()):

            with self.assertRaises(DataError):
                intrinio_data._read_company_data_point(
                    'NON-EXISTENT-TICKER', 'tag')

    '''
        Financial statement tests
    '''

    def test_historical_cashflow_stmt_with_api_exception(self):
        with patch.object(intrinio_data.fundamentals_api, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_cashflow_stmt(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    def test_historical_income_stmt_with_api_exception(self):
        with patch.object(intrinio_data.fundamentals_api, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_income_stmt(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    def test_historical_balacesheet_stmt_with_api_exception(self):
        with patch.object(intrinio_data.fundamentals_api, 'get_fundamental_standardized_financials',
                          side_effect=ApiException("Not Found")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(DataError):
                intrinio_data.get_historical_balance_sheet(
                    'NON-EXISTENT-TICKER', 2018, 2018, None)

    '''
        Stock Price Tests
    '''

    def test_daily_stock_prices_with_api_exception(self):
        with patch.object(intrinio_data.security_api, 'get_security_stock_prices',
                          side_effect=ApiException("Not Found")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(DataError):
                intrinio_data.get_daily_stock_close_prices(
                    'NON-EXISTENT-TICKER', datetime.date(2018, 1, 1), datetime.date(2019, 1, 1))

    def test_daily_stock_prices_with_other_exception(self):
        with patch.object(intrinio_data.security_api, 'get_security_stock_prices',
                          side_effect=KeyError("xxx")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(ValidationError):
                intrinio_data.get_daily_stock_close_prices(
                    'NON-EXISTENT-TICKER', datetime.date(2018, 1, 1), datetime.date(2019, 1, 1))

    def test_latest_stock_prices_invalid_lookback(self):
        with self.assertRaises(ValidationError):
            intrinio_data.get_latest_close_price(
                'AAPL', datetime.date(2018, 1, 1), 25)

    def test_latest_stock_prices_with_exception(self):
        with patch.object(intrinio_data.security_api, 'get_security_stock_prices',
                          side_effect=ApiException("Not Found")), \
                patch('support.financial_cache.cache', new=nop.Nop()):
            with self.assertRaises(DataError):
                intrinio_data.get_latest_close_price(
                    'XXX', datetime.date(2018, 1, 1), 5)
