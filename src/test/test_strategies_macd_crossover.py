"""Author: Mark Hanegraaff -- 2020

Testing class for the strategies.macd_crossover_strategy module
"""
import unittest
import pandas as pd
from unittest.mock import patch
from datetime import date
from support import constants, util
from model.ticker_list import TickerList
from exception.exceptions import ValidationError
from strategies.macd_crossover_strategy import MACDCrossoverStrategy
from connectors import intrinio_data
from support.configuration import Configuration


class TestStrategiesMACDCrossover(unittest.TestCase):
    """
        Testing class for the strategies.macd_crossover_strategy module
    """

    '''
        Constructor Tests
    '''

    ticker_file_path = "%s/djia30.json" % constants.TICKER_DATA_DIR
    ticker_list = TickerList.from_local_file(ticker_file_path)

    def test_from_configuration_invalid(self):
        with patch('support.constants.CONFIG_FILE_PATH', "./test/config-unittest-bad/"):
            bad_config = Configuration.from_local_config("bad-test-config.ini")
            with self.assertRaises(ValidationError):
                MACDCrossoverStrategy.from_configuration(bad_config, 'sa')

    def test_from_configuration_valid(self):

        ticker_list = TickerList.from_local_file(
            "%s/djia30.json" % (constants.APP_DATA_DIR))

        price_date = date(2020, 6, 3)

        with patch.object(util, 'get_business_date',
                          return_value=price_date), \
            patch.object(TickerList, 'from_s3',
                         return_value=ticker_list):

            strategy = MACDCrossoverStrategy.from_configuration(
                Configuration.from_local_config(constants.STRATEGY_CONFIG_FILE_NAME), 'sa')

            self.assertEqual(strategy.analysis_date, price_date)

    '''
        _analyze_security tests
    '''

    def test_analyze_security_1(self):
        '''
            Significant divergence. Both MACD and histogram positive
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = 10
        signal_line = 9

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_2(self):
        '''
            No significant divergence. Both MACD and histogram positive
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = 10
        signal_line = 9.9

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_3(self):
        '''
            Significant divergence. both MACD and Signal negative 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = -10
        signal_line = -9

        self.assertFalse(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_4(self):
        '''
            No significant divergence. both MACD and Signal negative 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = -10
        signal_line = -9.9

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_5(self):
        '''
            Significant divergence. both MACD positive, Signal negative 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = 1
        signal_line = -1

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_6(self):
        '''
            No Significant divergence. MACD positive, Signal negative 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = 0.01
        signal_line = -0.01

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_6(self):
        '''
            No Significant divergence. MACD negative, Signal positive 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = -1
        signal_line = 1

        self.assertFalse(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    def test_analyze_security_7(self):
        '''
            No Significant divergence. MACD negative, Signal positive 
        '''

        macd_strategy = MACDCrossoverStrategy(
            self.ticker_list, date(2020, 6, 10), 0.0016, 12, 26, 9)

        current_price = 100
        macd_line = -0.01
        signal_line = 0.01

        self.assertTrue(macd_strategy._analyze_security(
            current_price, macd_line, signal_line))

    price_dict = {
        "2020-06-08": 54.74
    }

    sma_dict = {
        "2020-06-08": 43.80299999999999
    }

    macd_dict = {
        "2020-06-08": {
            "macd_histogram": 0.9111766583116911,
            "macd_line": 2.085415403516656,
            "signal_line": 1.1742387452049647
        }
    }

    '''
        _read_price_metrics tests
    '''

    def test_read_price_metrics(self):
        with patch.object(intrinio_data, 'get_daily_stock_close_prices',
                          return_value=self.price_dict), \
            patch.object(intrinio_data, 'get_sma_indicator',
                         return_value=self.sma_dict), \
            patch.object(intrinio_data, 'get_macd_indicator',
                         return_value=self.macd_dict):

            macd_strategy = MACDCrossoverStrategy(
                self.ticker_list, date(2020, 6, 8), 0.0016, 12, 26, 9)

            (current_price, macd_line,
             signal_line) = macd_strategy._read_price_metrics('AAPL')

            self.assertEqual(current_price, 54.74)
            self.assertEqual(macd_line, 2.085415403516656)
            self.assertEqual(signal_line, 1.1742387452049647)

    def test_read_price_metrics_with_exception(self):
        with patch.object(intrinio_data, 'get_daily_stock_close_prices',
                          return_value={
                "2020-06-09": 54.74
                          }), \
            patch.object(intrinio_data, 'get_sma_indicator',
                         return_value={
                "2020-06-09": 43.80299999999999
                             }), \
            patch.object(intrinio_data, 'get_macd_indicator',
                         return_value={
                "2020-06-09": {
                "macd_histogram": 9111766583116911,
                "macd_line": 2.085415403516656,
                "signal_line": 1.1742387452049647
                }
                             }):

            ticker_file_path = "%s/djia30.json" % constants.TICKER_DATA_DIR

            macd_strategy = MACDCrossoverStrategy(
                self.ticker_list, date(2020, 6, 8), 0.0016, 12, 26, 9)

            with self.assertRaises(ValidationError):
                macd_strategy._read_price_metrics('AAPL')

    '''
        generate_recommendation tests
        Tests that the recommendation set is properly constructed, specifially
        in terms of using the correct dates
    '''

    def test_recommendation_set_dates(self):

        price_date = date(2020, 6, 8)
        with patch.object(intrinio_data, 'get_daily_stock_close_prices',
                          return_value=self.price_dict), \
            patch.object(intrinio_data, 'get_sma_indicator',
                         return_value=self.sma_dict), \
            patch.object(intrinio_data, 'get_macd_indicator',
                         return_value=self.macd_dict):

            strategy = MACDCrossoverStrategy(
                self.ticker_list, price_date, 0.0016, 12, 26, 9)

            strategy.generate_recommendation()

            recommendation_set = strategy.recommendation_set

            self.assertEqual(recommendation_set.model[
                'valid_from'], str(date(2020, 6, 8)))
            self.assertEqual(recommendation_set.model[
                'valid_to'], str(date(2020, 6, 8)))
            self.assertEqual(recommendation_set.model[
                'price_date'], str(date(2020, 6, 8)))
