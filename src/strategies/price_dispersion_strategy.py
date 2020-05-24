"""Author: Mark Hanegraaff -- 2020
"""

import pandas as pd
from datetime import datetime, timedelta
from connectors import intrinio_data, intrinio_util
import logging
from support import util
from exception.exceptions import BaseError, ValidationError, DataError
from model.recommendation_set import SecurityRecommendationSet


class PriceDispersionStrategy():
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
            "valid_from": "2020-03-01T00:00:00-05:00",
            "valid_to": "2020-03-31T00:00:00-04:00",
            "price_date": "2020-03-31T00:00:00-04:00",
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

    def __init__(self, ticker_list: list, data_year: int, data_month: int, output_size: int):
        """
            Initializes the class with the ticker list, a year and a month.

            The year and month are used to set the context of the analysis,
            meaning that financial data will be used for that year/month.
            This is done to allow the analysis to be run in the past and test the
            quality of the results.


            Parameters
            ------------
            ticker_list : list of tickers to be included in the analisys
            ticker_source_name : The source of the ticker list. E.g. DOW30, or SP500
            year : analysis year
            month : analysis month
            output_size : number of recommended securities that will be returned
                by this strategy

        """

        if (ticker_list is None or len(ticker_list) == 0):
            raise ValidationError("No ticker list was supplied", None)

        if len(ticker_list) < 2:
            raise ValidationError(
                "You must supply at least 2 ticker symbols", None)

        if output_size <= 0:
            raise ValidationError(
                "Output size must be at least 1", None)

        (self.analysis_start_date, self.analysis_end_date) = intrinio_util.get_month_date_range(
            data_year, data_month)

        if (self.analysis_end_date > datetime.now()):
            logging.debug("Setting analysis end date to 'today'")
            self.analysis_end_date = datetime.now()

        self.ticker_list = ticker_list

        self.output_size = output_size
        self.data_date = "%d-%d" % (data_year, data_month)

        self.recommendation_set = None
        self.raw_dataframe = None
        self.recommendation_dataframe = None

    def __load_financial_data__(self):
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
        logging.debug("Analysis price date is %s" % (dde.strftime("%Y-%m-%d")))

        for ticker in self.ticker_list:
            try:
                target_price_sdtdev = intrinio_data.get_target_price_std_dev(ticker, dds, dde)[
                    year][month]
                target_price_avg = intrinio_data.get_target_price_mean(ticker, dds, dde)[
                    year][month]
                dispersion_stdev_pct = target_price_sdtdev / target_price_avg * 100

                analysis_price = intrinio_data.get_latest_close_price(ticker, dde, 5)[
                    1]

                analyst_expected_return = (
                    target_price_avg - analysis_price) / analysis_price

                financial_data['analysis_period'].append(self.data_date)
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

        financial_data = self.__load_financial_data__()

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
        valid = self.analysis_end_date + timedelta(days=1)

        (valid_from, valid_to) = intrinio_util.get_month_date_range(
            valid.year, valid.month)

        self.recommendation_set = SecurityRecommendationSet.from_parameters(datetime.now(), valid_from, valid_to, self.analysis_end_date,
                                                                            self.STRATEGY_NAME, "US Equities", priced_securities)
