"""Author: Mark Hanegraaff -- 2020

Testing class for the strategies.price_dispersion module
"""
import unittest
import pandas as pd
from unittest.mock import patch
from intrinio_sdk.rest import ApiException
from connectors import intrinio_data
from datetime import date, datetime
from exception.exceptions import ValidationError, DataError
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from model.ticker_list import TickerList
from support import constants, util
from support.configuration import Configuration


class TestStrategiesPriceDispersion(unittest.TestCase):
    """
        Testing class for the strategies.price_dispersion module
    """

    '''
        Constructor tests
    '''

    def test_init_bad_period(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(TickerList.from_dict(
                {
                    "list_name": "DOW30",
                    "list_type": "US_EQUITIES",
                    "comparison_symbol": "DIA",
                    "ticker_symbols": ['AAPL', 'V']
                }
            ), 'invalid_period', date(2020, 6, 10), 3)

    def test_init_no_price_date(self):
        PriceDispersionStrategy(TickerList.from_dict(
            {
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": ['AAPL', 'V']
            }
        ), '2020-05', None, 3)

    def test_init_no_tickers(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(None, '2020-02', date(2020, 6, 10), 3)

    def test_init_empty_ticker_list(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(TickerList.from_dict(
                {
                    "list_name": "DOW30",
                    "list_type": "US_EQUITIES",
                    "comparison_symbol": "DIA",
                    "ticker_symbols": []
                }
            ), '2020-02', date(2020, 6, 10), 3)

    def test_init_too_few_tickers(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(TickerList.from_dict(
                {
                    "list_name": "DOW30",
                    "list_type": "US_EQUITIES",
                    "comparison_symbol": "DIA",
                    "ticker_symbols": ['AAPL']
                }), '2020-02', date(2020, 6, 10), 3)

    def test_init_output_size_too_small(self):
        with self.assertRaises(ValidationError):
            PriceDispersionStrategy(TickerList.from_dict({
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": ['AAPL', 'V']
            }), '2020-02', date(2020, 6, 10), 0)

    def test_init_enough_tickers(self):
        PriceDispersionStrategy(TickerList.from_dict({
            "list_name": "DOW30",
            "list_type": "US_EQUITIES",
            "comparison_symbol": "DIA",
            "ticker_symbols": ['AAPL', 'V']
        }), '2020-02', date(2020, 6, 10), 3)

    '''
        from_configuration tests
    '''

    def test_from_configuration_invalid(self):
        with patch('support.constants.CONFIG_FILE_PATH', "./test/config-unittest-bad/"):
            with self.assertRaises(ValidationError):
                PriceDispersionStrategy.from_configuration(
                    Configuration.from_local_config("bad-test-config.ini"), 'sa')

    def test_from_configuration_valid(self):

        ticker_list = TickerList.from_local_file(
            "%s/djia30.json" % (constants.APP_DATA_DIR))

        with patch.object(util, 'get_business_date',
                          return_value=date(2020, 6, 3)), \
            patch.object(pd, 'to_datetime',
                         return_value=datetime(2020, 6, 19)), \
            patch.object(TickerList, 'from_s3',
                         return_value=ticker_list):

            strategy = PriceDispersionStrategy.from_configuration(
                Configuration.from_local_config(constants.STRATEGY_CONFIG_FILE_NAME), 'sa')

            self.assertEqual(strategy.analysis_start_date, date(2020, 5, 1))
            self.assertEqual(strategy.analysis_end_date, date(2020, 5, 31))
            self.assertEqual(strategy.current_price_date, date(2020, 6, 3))

        '''
            _load_financial_data tests
        '''

    def test_api_exception(self):
        with patch.object(intrinio_data.COMPANY_API, 'get_company_historical_data',
                          side_effect=ApiException("Not Found")):

            strategy = PriceDispersionStrategy(TickerList.from_dict({
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": ['AAPL', 'V']
            }), '2000-05', date(2000, 6, 10), 3)

            with self.assertRaises(DataError):
                strategy._load_financial_data()

    '''
        generate_recommendation tests
        Tests that the recommendation set is properly constructed, specifially
        in terms of using the correct dates
    '''

    financial_data = {
        'analysis_period': [datetime.now()],
        'ticker': ['AAPL'],
        'analysis_price': [100],
        'target_price_avg': [100],
        'dispersion_stdev_pct': [20],
        'analyst_expected_return': [0.5]
    }

    def test_recommendation_set_price_date_after_analysisperiod(self):
        with patch.object(PriceDispersionStrategy, '_load_financial_data',
                          return_value=self.financial_data):

            strategy = PriceDispersionStrategy(TickerList.from_dict({
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": ['AAPL', 'V']
            }), '2020-05', date(2020, 6, 10), 3)

            strategy.generate_recommendation()

            recommendation_set = strategy.recommendation_set

            self.assertEqual(recommendation_set.model[
                'valid_from'], str(date(2020, 6, 1)))
            self.assertEqual(recommendation_set.model[
                'valid_to'], str(date(2020, 6, 30)))
            self.assertEqual(recommendation_set.model[
                'price_date'], str(date(2020, 5, 31)))

    def test_recommendation_set_price_date_during_analysisperiod(self):
        with patch.object(PriceDispersionStrategy, '_load_financial_data',
                          return_value=self.financial_data):

            price_date = date(2020, 6, 10)

            strategy = PriceDispersionStrategy(TickerList.from_dict({
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": ['AAPL', 'V']
            }), '2020-06', price_date, 3)

            strategy.generate_recommendation()

            recommendation_set = strategy.recommendation_set

            self.assertEqual(recommendation_set.model[
                'valid_from'], str(date(2020, 7, 1)))
            self.assertEqual(recommendation_set.model[
                'valid_to'], str(date(2020, 7, 31)))
            self.assertEqual(recommendation_set.model[
                'price_date'], str(date(2020, 6, 10)))

    def test_recommendation_set_price_date_before_analysisperiod(self):
        with patch.object(PriceDispersionStrategy, '_load_financial_data',
                          return_value=self.financial_data):

            price_date = date(2020, 5, 10)

            with self.assertRaises(ValidationError):
                strategy = PriceDispersionStrategy(TickerList.from_dict({
                    "list_name": "DOW30",
                    "list_type": "US_EQUITIES",
                    "comparison_symbol": "DIA",
                    "ticker_symbols": ['AAPL', 'V']
                }), '2020-06', price_date, 3)
