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
        This strategy uses a combination of SMA and MACD indicator to detect whether 
        a stock is bullish or bearish. A bullish pattern is identified when a stock price
        is above the moving average, and when the macd line
        crosses over the signal line. When this happens, the security will be
        included in the recommendation set, otherwise it will not.

        Attributes
        ----------
        MACD_SIGNAL_CROSSOVER_FACTOR: float
            A factor used to calculate the threshold to determine when
            the signal has dipped too far below the signal line.
    '''

    STRATEGY_NAME = "MACD_CROSSOVER"
    CONFIG_SECTION = "macd_crossover_strategy"
    S3_RECOMMENDATION_SET_OBJECT_NAME = constants.S3_MACD_CROSSOVER_RECOMMENDATION_SET_OBJECT_NAME

    MACD_SIGNAL_CROSSOVER_FACTOR = 0.1

    def __init__(self, ticker_list: object, analysis_date: date, sma_period: int, macd_fast_period: int, macd_slow_period: int, macd_signal_period: int):
        '''
            Initializes the strategy by supplying all parameters directly

            Parameters
            ----------
            ticker_list: TickerList
                TickerList object representing the input to the strategy
            analysis_date: date
                Analysis (price) date
            sma_period: int
                The Simple Moving average perdiod in days, e.g. 50
            macd_fast_period: int
                MACD fast moving period in days, e.g. 12
            macd_slow_period: int
                MACD slow moving period in days, e.g. 24
            macd_signal_period: int
                MACD signal period in days, e.g. 9
        '''

        self.ticker_list = ticker_list
        self.analysis_date = analysis_date
        self.sma_period = sma_period
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

            sma_period = int(config_params['sma_period'])
            ticker_file_name = config_params['ticker_list_file_name']
            macd_fast_period = int(config_params['macd_fast_period'])
            macd_slow_period = int(config_params['macd_slow_period'])
            macd_signal_period = int(config_params['macd_signal_period'])
        except Exception as e:
            raise ValidationError(
                "Could not read MACD Crossover Strategy configuration parameters", e)
        finally:
            configuration.close()

        ticker_list = TickerList.try_from_s3(app_ns, ticker_file_name)

        return cls(ticker_list, analysis_date, sma_period, macd_fast_period, macd_slow_period, macd_signal_period)

    def _read_price_metrics(self, ticker_symbol: str):
        '''
            Helper function that downloads the necessary data to perfom the MACD Crossover calculation.
            Most data includes a short history to help filter out false signals.

            Returns
            -------
            A Tuple with the following elements:
            current_price: float
                The Current price for the ticker symbol
            sma_list: list
                The part 3 days of Simple Moving average prices
            macd_lines: list
                The past 3 days of MACD values
            signal_lines
                The past 3 days of MACD Singal values

        '''

        lookback_days = 3

        lookback_date = self.analysis_date - timedelta(days=7)

        dict_key = self.analysis_date.strftime("%Y-%m-%d")

        current_price_dict = intrinio_data.get_daily_stock_close_prices(
            ticker_symbol, self.analysis_date, self.analysis_date
        )

        # Get last 3 days of the moving average
        sma_dict = intrinio_data.get_sma_indicator(
            ticker_symbol, lookback_date, self.analysis_date, self.sma_period
        )
        if not dict_key in sma_dict:
            raise DataError("Unable to download Simple moving average for (%s, %s)" % (
                ticker_symbol, dict_key), None)
        sma_ordered_dict = OrderedDict(sorted(sma_dict.items(), reverse=True))

        # Get last 3 days of macd and singal values
        macd_dict = intrinio_data.get_macd_indicator(
            ticker_symbol, lookback_date, self.analysis_date, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period
        )

        if not dict_key in macd_dict:
            raise DataError("Unable to download MACD values for (%s, %s)" % (
                ticker_symbol, dict_key), None)

        macd_line_dict = OrderedDict(
            sorted(macd_dict.items(), reverse=True))
        signal_line_dict = OrderedDict(
            sorted(macd_dict.items(), reverse=True))

        try:
            current_price = current_price_dict[dict_key]

            sma_list = [sma_ordered_dict.popitem(
                last=False)[1] for _ in range(0, lookback_days)]

            macd_lines = [macd_line_dict.popitem(
                last=False)[1]['macd_line'] for _ in range(0, lookback_days)]
            signal_lines = [signal_line_dict.popitem(
                last=False)[1]['signal_line'] for _ in range(0, lookback_days)]

        except Exception as e:
            raise ValidationError(
                "Could not read pricing data for %s" % ticker_symbol, e)

        return (current_price, sma_list, macd_lines, signal_lines)

    def _analyze_security(self, current_price: float, sma_list: list, macd_lines: float, signal_lines: float):
        '''
            Helper function that, based on the analysis data, determines whether
            a positive MACD crossover has occurred or not.

            The basic idea is that the if price is above the SMA, and MACD is above the
            signal the stock is bullish. A bullish pattern triggers a buy signal, while a crash
            triggers a sell.

            But identifying crossovers isn't so obvious; sometimes these value trend closely to each other
            and so it may be necessary to look at historical data too.

            To account for that, the method includes a threshold to prevent the buy/sell signal 
            from flipping too frequently when values are close. 

            Specifically before identifying a crash:
            1) Ensure that if current price < SMA it has been so for at least the
                past 3 days.
            2) Ensure that if macd dips below the signal, but it still close to it
                (within a threshold) it has been so for at least the past 3 days

            Returns
            -------
            True if the security is bullish, otherwise False
        '''

        # Price must have ben above sma for 3 days
        for sma_price in sma_list:
            if current_price < sma_price:
                return False

        latest_macd = macd_lines[0]
        latest_signal = signal_lines[0]

        crossover_threshold = abs(
            latest_macd * self.MACD_SIGNAL_CROSSOVER_FACTOR)

        if (latest_macd > latest_signal):
            return True
        elif latest_macd > (latest_signal - crossover_threshold):
            for i in range(0, len(macd_lines)):
                if macd_lines[i] > signal_lines[i]:
                    return True

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
            'sma': [],
            'macd': [],
            'signal': [],
            'divergence': [],
            'recommendation': []
        }

        recommended_securities = {}

        for ticker_symbol in self.ticker_list.ticker_symbols:
            (current_price, sma_list, macd_lines, signal_lines) = self._read_price_metrics(
                ticker_symbol)

            buy_sell_indicator = self._analyze_security(
                current_price, sma_list, macd_lines, signal_lines)

            analysis_data['ticker_symbol'].append(ticker_symbol)
            analysis_data['price'].append(current_price)
            analysis_data['sma'].append(sma_list[0])
            analysis_data['macd'].append(macd_lines[0])
            analysis_data['signal'].append(signal_lines[0])
            analysis_data['divergence'].append(macd_lines[0] - signal_lines[0])
            if buy_sell_indicator == True:
                analysis_data['recommendation'].append("BUY")
                recommended_securities[ticker_symbol] = current_price
            else:
                analysis_data['recommendation'].append("SELL")

            # log.info("%s: (%.3f, %s, %s, %s) --> %s" % (ticker_symbol, current_price, ["{0:0.2f}".format(i) for i in sma_list], ["{0:0.2f}".format(i) for i in macd_lines], ["{0:0.2f}".format(i) for i in signal_lines],
            #                                                      buy_sell_indicator))

        self.raw_dataframe = pd.DataFrame(analysis_data)
        self.raw_dataframe = self.raw_dataframe.sort_values(
            ['recommendation', 'divergence'], ascending=(True, False))

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
        log.info("SMA Period: %d, MACD Parameters: (%d, %d, %d)" % (
            self.sma_period, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period))
        print(self.raw_dataframe.to_string(index=False))
        log.info(util.format_dict(self.recommendation_set.model))
