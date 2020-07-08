"""Author: Mark Hanegraaff -- 2020
"""

import logging
import pandas as pd
import pandas_market_calendars as mcal
import dateutil.parser as parser
from datetime import datetime, timedelta, date, time
from collections import OrderedDict
from support import util, constants
from strategies.base_strategy import BaseStrategy
from strategies import calculator
from model.recommendation_set import SecurityRecommendationSet
from model.ticker_list import TickerList
from exception.exceptions import ValidationError, DataError
from connectors import intrinio_data, intrinio_util

log = logging.getLogger()


class MACDCrossoverStrategy(BaseStrategy):
    '''
        This strategy uses the MACD signal to determine whether a stock is bullish or
        bearish. A Bullish stock will signal a buy and will be included in the recommendation set, 
        while a bearish stock will signal a sell and be excluded.

        The calculation starts by determining whether the macd divergence (histogram) is significant 
        or not by dividing the histogram by the current price and comparing it to a threshold

        Then the macd and histogram values are examined:

        A bullish signal starts when the macd and histograms are below 0, but the
        histogram divergence is no longer significant, therefore it's about to crossover.

        A bearish signal starts when the macd is above 0 and the histogram has dipped
        significantly into negative territory

        This stragegy is prone to false signals and because of that, it is most effective when
        used in combination with proper PNL management.
    '''

    STRATEGY_NAME = "MACD_CROSSOVER"
    CONFIG_SECTION = "macd_crossover_strategy"
    S3_RECOMMENDATION_SET_OBJECT_NAME = constants.S3_MACD_CROSSOVER_RECOMMENDATION_SET_OBJECT_NAME

    def __init__(self, ticker_list: object, analysis_date: date, divergence_factor_threshold: float, macd_fast_period: int, macd_slow_period: int, macd_signal_period: int):
        '''
            Initializes the strategy by supplying all parameters directly

            Parameters
            ----------
            ticker_list: TickerList
                TickerList object representing the input to the strategy
            analysis_date: date
                Analysis (price) date
            divergence_factor_threshold: float
                A threshold used to indicate when the level of divergence is
                significant or not
            macd_fast_period: int
                MACD fast moving period in days, e.g. 12
            macd_slow_period: int
                MACD slow moving period in days, e.g. 24
            macd_signal_period: int
                MACD signal period in days, e.g. 9
        '''

        self.ticker_list = ticker_list
        self.analysis_date = analysis_date
        self.divergence_factor_threshold = divergence_factor_threshold
        self.macd_fast_period = macd_fast_period
        self.macd_slow_period = macd_slow_period
        self.macd_signal_period = macd_signal_period

    @classmethod
    def from_configuration(cls, configuration: object, app_ns: str):
        '''
            See BaseStrategy.from_configuration for documentation
        '''

        analysis_date = util.get_business_date(
            constants.BUSINESS_DATE_DAYS_LOOKBACK, constants.BUSINESS_DATE_CUTOVER_TIME)

        try:
            config_params = dict(configuration.config[cls.CONFIG_SECTION])

            ticker_file_name = config_params['ticker_list_file_name']
            divergence_factor_threshold = float(
                config_params['divergence_factor_threshold'])
            macd_fast_period = int(config_params['macd_fast_period'])
            macd_slow_period = int(config_params['macd_slow_period'])
            macd_signal_period = int(config_params['macd_signal_period'])
        except Exception as e:
            raise ValidationError(
                "Could not read MACD Crossover Strategy configuration parameters", e)
        finally:
            configuration.close()

        ticker_list = TickerList.try_from_s3(app_ns, ticker_file_name)

        return cls(ticker_list, analysis_date, divergence_factor_threshold, macd_fast_period, macd_slow_period, macd_signal_period)

    def _read_price_metrics(self, ticker_symbol: str):
        '''
            Helper function that downloads the data required by the strategy.

            Returns
            -------
            A Tuple with the following elements:
            current_price: float
                The Current price for the ticker symbol
            macd_lines: list
                The past 3 days of MACD values
            signal_lines
                The past 3 days of MACD Singal values

        '''
        dict_key = self.analysis_date.strftime("%Y-%m-%d")

        current_price_dict = intrinio_data.get_daily_stock_close_prices(
            ticker_symbol, self.analysis_date, self.analysis_date
        )

        macd_dict = intrinio_data.get_macd_indicator(
            ticker_symbol, self.analysis_date, self.analysis_date, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period
        )

        try:
            current_price = current_price_dict[dict_key]
            macd_line = macd_dict[dict_key]['macd_line']
            signal_line = macd_dict[dict_key]['signal_line']
        except Exception as e:
            raise ValidationError(
                "Could not read pricing data for %s" % ticker_symbol, e)

        return (current_price, macd_line, signal_line)

    def _analyze_security(self, current_price: float, macd_line: float, signal_line: float):
        '''
            Helper function that, based on the price and MACD data determines if a security
            is bullish or bearish. strategy's calculation is encapsulated here.

            Returns
            -------
            True if the security is bullish, otherwise False
        '''

        latest_histogram = macd_line - signal_line

        divergence_factor = abs(
            latest_histogram / current_price)

        significant_divergence = divergence_factor > self.divergence_factor_threshold

        if macd_line > 0 and latest_histogram > 0:
            return True
        if macd_line > 0 and latest_histogram < 0 and not significant_divergence:
            return True
        elif macd_line < 0 and latest_histogram > 0:
            return True
        elif macd_line < 0 and latest_histogram < 0 and not significant_divergence:
            return True
        else:
            return False

    def generate_recommendation(self):
        '''
            Analyzes all securitues supplied in the ticker list and returns a SecurityRecommendationSet
            object containing all stocks with a positive MACD crossover. These are stocks
            that are bullish and have positive momentum behind them.

            internally sets the self.recommendation_set object

        '''

        analysis_data = {
            'ticker_symbol': [],
            'price': [],
            'macd': [],
            'signal': [],
            'divergence': [],
            'momentum': []
        }

        recommended_securities = {}

        for ticker_symbol in self.ticker_list.ticker_symbols:
            (current_price, macd_line, signal_line) = self._read_price_metrics(
                ticker_symbol)

            buy_sell_indicator = self._analyze_security(
                current_price, macd_line, signal_line)

            analysis_data['ticker_symbol'].append(ticker_symbol)
            analysis_data['price'].append(current_price)
            analysis_data['macd'].append(macd_line)
            analysis_data['signal'].append(signal_line)
            analysis_data['divergence'].append(macd_line - signal_line)
            if buy_sell_indicator == True:
                analysis_data['momentum'].append("BULLISH")
                recommended_securities[ticker_symbol] = current_price
            else:
                analysis_data['momentum'].append("BEARISH")

        self.raw_dataframe = pd.DataFrame(analysis_data)
        self.raw_dataframe = self.raw_dataframe.sort_values(
            ['momentum', 'divergence'], ascending=(False, False))

        valid_from = valid_to = self.analysis_date

        self.recommendation_set = SecurityRecommendationSet.from_parameters(
            datetime.now(), valid_from, valid_to, self.analysis_date, self.STRATEGY_NAME,
            "US_EQUITIES", recommended_securities
        )

    def display_results(self):
        '''
            Display the final recommendation and the intermediate results of the strategy
        '''

        log.info("Displaying results of MACD strategy")
        log.info("Analysis Date: %s" % self.analysis_date.strftime("%Y-%m-%d"))
        log.info("Divergence Tolerance Factor: %f, MACD Parameters: (%d, %d, %d)" % (
            self.divergence_factor_threshold, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period))
        print(self.raw_dataframe.to_string(index=False))
        log.info(util.format_dict(self.recommendation_set.model))
