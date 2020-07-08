"""Author: Mark Hanegraaff -- 2020
"""

import pandas as pd
from datetime import datetime, date, timedelta, timezone
from connectors import intrinio_data, intrinio_util
import logging
from support import util, constants
from exception.exceptions import BaseError, ValidationError, DataError
from model.recommendation_set import SecurityRecommendationSet
from model.ticker_list import TickerList
from strategies.base_strategy import BaseStrategy
from strategies import calculator

log = logging.getLogger()


class PriceDispersionStrategy(BaseStrategy):
    """
        An trading strategy based on analyst target price agreement measured as
        the price dispersion, described in papers like these:

        /doc/Consensus-Analyst-Target-Prices.pdf
        /doc/Dispersion-Analysts-Target-Prices-Stock-Returns.pdf
        /doc/Predictive-Power-Analyst-Price-Target-Dispersion.pdf

        Specifically, given a list ticker symbols, it will return a recommendation
        that consists of securities with the highest price dispersion (lowest analyst agreement)
        and highest price target. In other words recommendations are based on
        stocks where analyst can't seem to agree on the target price

        The recommendation set is represented as a JSON document like this:

        {
            "set_id": "bda2de4e-7ec6-11ea-86e7-acbc329ef75f",
            "creation_date": "2020-04-15T03:11:03.841242+00:00",
            "valid_from": "2020-03-01",
            "valid_to": "2020-03-31",
            "price_date": "2020-03-31",
            "strategy_name": "PRICE_DISPERSION",
            "security_type": "US Equities",
            "securities_set": [
                {
                    "ticker_symbol": "BA",
                    "price": 152.28
                },
                {
                    "ticker_symbol": "XOM",
                    "price": 37.5
                },
                {
                    "ticker_symbol": "GE",
                    "price": 7.89
                }
            ]
        }
    """

    STRATEGY_NAME = "PRICE_DISPERSION"
    CONFIG_SECTION = "price_dispersion_strategy"
    S3_RECOMMENDATION_SET_OBJECT_NAME = constants.S3_PRICE_DISPERSION_RECOMMENDATION_SET_OBJECT_NAME

    def __init__(self, ticker_list: list, analysis_period: str, current_price_date: date, output_size: int):
        """
            Initializes the strategy given the ticker list, analysis period
            and output size.

            The period is used to determine the range of financial data required
            to perform the analysis, while the output size will limit the number
            of securities that are recommended by the strategy.

            Parameters
            ------------
            ticker_list : list of tickers to be included in the analisys
            analysis_period: The analysis period as a string. E.g. '2020-06'
            output_size : number of recommended securities that will be returned
                by this strategy
        """

        if ticker_list == None or len(ticker_list.ticker_symbols) < 2:
            raise ValidationError(
                "Ticker List must contain at least 2 symbols", None)

        if output_size == 0:
            raise ValidationError(
                "Output size must be at least 1", None)

        try:
            self.analysis_period = pd.Period(analysis_period, 'M')
        except Exception as e:
            raise ValidationError("Could not parse Analysis Period", e)

        self.ticker_list = ticker_list

        self.output_size = output_size

        if (current_price_date == None):
            business_date = self.current_price_date = util.get_business_date(
                constants.BUSINESS_DATE_DAYS_LOOKBACK, constants.BUSINESS_DATE_CUTOVER_TIME)

            self.current_price_date = business_date
        else:
            self.current_price_date = current_price_date

        (self.analysis_start_date, self.analysis_end_date) = intrinio_util.get_month_period_range(
            self.analysis_period)

        if (self.analysis_start_date > self.current_price_date):
            raise ValidationError("Price Date: [%s] must be greater than the Analysis Start Date [%s]" % (
                self.current_price_date, self.analysis_start_date), None)

        if (self.analysis_end_date > self.current_price_date):
            logging.debug("Setting analysis end date to 'today'")
            self.analysis_end_date = self.current_price_date

        self.recommendation_set = None
        self.raw_dataframe = None
        self.recommendation_dataframe = None

    @classmethod
    def from_configuration(cls, configuration: object, app_ns: str):
        '''
            See BaseStrategy.from_configuration for documentation
        '''
        today = pd.to_datetime('today').date()

        try:
            config_params = dict(configuration.config[cls.CONFIG_SECTION])

            ticker_file_name = config_params['ticker_list_file_name']
            output_size = int(config_params['output_size'])
        except Exception as e:
            raise ValidationError(
                "Could not read MACD Crossover Strategy configuration parameters", e)

        ticker_list = TickerList.try_from_s3(app_ns, ticker_file_name)
        analysis_period = (
            pd.Period(today, 'M') - 1).strftime("%Y-%m")

        current_price_date = util.get_business_date(
            constants.BUSINESS_DATE_DAYS_LOOKBACK, constants.BUSINESS_DATE_CUTOVER_TIME)

        return cls(ticker_list, analysis_period, current_price_date, output_size)

    def _load_financial_data(self):
        """
            loads the raw financial required by this strategy and returns it as
            a dictionary suitable for Pandas processing.

            Returns
            ------------
            A Dictionary with the following format.

            {
                'analysis_period': [],
                'ticker': [],
                'analysis_price': [],
                'target_price_avg': [],
                'dispersion_stdev_pct': [],
                'analyst_expected_return': []
            }

            Raises
            ------------
            DataError in case financial data could not be loaed for any
            securities
        """

        logging.debug("Loading financial data for %s strategy" %
                      self.STRATEGY_NAME)

        financial_data = {
            'analysis_period': [],
            'ticker': [],
            'analysis_price': [],
            'target_price_avg': [],
            'dispersion_stdev_pct': [],
            'analyst_expected_return': []
        }

        dds = self.analysis_start_date
        dde = self.analysis_end_date
        year = dds.year
        month = dds.month

        at_least_one = False

        logging.debug("Analysis date range is %s, %s" %
                      (dds.strftime("%Y-%m-%d"), dde.strftime("%Y-%m-%d")))
        logging.debug("Analysis price date is %s" %
                      (self.current_price_date.strftime("%Y-%m-%d")))

        for ticker in self.ticker_list.ticker_symbols:
            try:
                target_price_sdtdev = intrinio_data.get_zacks_target_price_std_dev(ticker, dds, dde)[
                    year][month]
                target_price_avg = intrinio_data.get_zacks_target_price_mean(ticker, dds, dde)[
                    year][month]
                dispersion_stdev_pct = target_price_sdtdev / target_price_avg * 100

                analysis_price = intrinio_data.get_latest_close_price(ticker, dde, 5)[
                    1]

                analyst_expected_return = (
                    target_price_avg - analysis_price) / analysis_price

                financial_data['analysis_period'].append(self.analysis_period)
                financial_data['ticker'].append(ticker)
                financial_data['analysis_price'].append(analysis_price)
                financial_data['target_price_avg'].append(target_price_avg)
                financial_data['dispersion_stdev_pct'].append(
                    dispersion_stdev_pct)
                financial_data['analyst_expected_return'].append(
                    analyst_expected_return)

                at_least_one = True
            except BaseError as be:
                logging.debug(
                    "%s will not be factored in recommendation, because: %s" % (ticker, str(be)))
            except Exception as e:
                raise DataError(
                    "Could not read %s financial data" % (ticker), e)

        if not at_least_one:
            raise DataError(
                "Could not load financial data for any if the supplied tickers", None)

        return financial_data

    def generate_recommendation(self):
        """
            Applies the price dispersion algorithm and sets the following 
            instance variables:

            self.recommendation_set
                A SecurityRecommendationSet object with the current 
                recommendation
            self.raw_dataframe
                Dataframe with all stocks sorted into deciles. Useful for
                displaying intermediate results.
            self.recommendation_dataframe
                A Dataframe containing just the recommended stocks

            Returns
            ------------
            None
        """

        financial_data = self._load_financial_data()

        self.raw_dataframe = pd.DataFrame(financial_data)
        pd.options.display.float_format = '{:.3f}'.format

        # sort the dataframe into deciles
        self.raw_dataframe['decile'] = pd.qcut(
            financial_data['dispersion_stdev_pct'], 10, labels=False, duplicates='drop')
        self.raw_dataframe = self.raw_dataframe.sort_values(
            ['decile', 'analyst_expected_return'], ascending=(False, False))

        self.recommendation_dataframe = self.raw_dataframe.head(self.output_size).drop(
            ['decile', 'target_price_avg', 'dispersion_stdev_pct', 'analyst_expected_return'], axis=1)

        # price the recommended securitues
        priced_securities = {}
        for row in self.recommendation_dataframe.itertuples(index=False):
            priced_securities[row.ticker] = row.analysis_price

        # determine the recommendation valid date range
        (valid_from, valid_to) = intrinio_util.get_month_period_range(
            self.analysis_period + 1)

        self.recommendation_set = SecurityRecommendationSet.from_parameters(datetime.now(), valid_from, valid_to, self.analysis_end_date,
                                                                            self.STRATEGY_NAME, "US Equities", priced_securities)

    def display_results(self):
        '''
            Displays the results of the strategy to the screen.
            Specifically displays the ranking of the securities using
            a Pandas Dataframe and the resulting recommendation set.
        '''
        log.info("Calculating Current Returns")
        raw_dataframe = calculator.mark_to_market(
            self.raw_dataframe, 'ticker', 'analysis_price', self.current_price_date)
        recommendation_dataframe = calculator.mark_to_market(
            self.recommendation_dataframe, 'ticker', 'analysis_price', self.current_price_date)

        log.info("")
        log.info("Recommended Securities")
        log.info(util.format_dict(self.recommendation_set.to_dict()))
        log.info("")

        log.info("Recommended Securities Return: %.2f%%" %
                 (recommendation_dataframe['actual_return'].mean() * 100))
        log.info("Average Return: %.2f%%" %
                 (raw_dataframe['actual_return'].mean() * 100))
        log.info("")
        log.info("Analysis Period - %s, Actual Returns as of: %s" %
                 (self.analysis_period, self.current_price_date))

        # Using the logger will mess up the header of this table
        print(raw_dataframe[['analysis_period', 'ticker', 'dispersion_stdev_pct',
                             'analyst_expected_return', 'actual_return', 'decile']].to_string(index=False))
