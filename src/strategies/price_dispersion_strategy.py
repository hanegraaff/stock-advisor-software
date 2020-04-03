import pandas as pd
from datetime import datetime
from data_provider import intrinio_data, intrinio_util
import logging
from support import util
from exception.exceptions import BaseError, ValidationError, DataError
from model.recommendation_set import SecurityRecommendationSet


class PriceDispersionStrategy():
    """
        An invenstment strategy based on analyst targer price agreement measured as
        the price dispersion, as detailed in this paper:

        https://www8.gsb.columbia.edu/faculty-research/sites/faculty-research/files/FRANK%20ZHANG%20PAPER%20PSZ_20190913.pdf

        Specifically, given a list ticker symbols, it will return a recommendation
        that consists of securities with the lowest price dispersion (highest analyst agreement)
        and highest price target.

        The recommendation set is represented as a JSON document like this:

        {
            "set_id": uuid (str),
            "creation_date": ISO8601 Date - UTC Timezone,
            "analysis_start_date": ISO8601 Date,
            "analysis_end_date": ISO8601 Date,
            "price_date": ISO8601 Date - UTC Timezone,
            "strategy_name": str,
            "security_type": str
            "security_set": {
                "str": float,
                "str": float,
                "str": float
            }
        }
    """


    STRATEGY_NAME = "PRICE_DISPERSION"

    def __init__(self, ticker_list : list, data_year : int, data_month : int, portfolio_size : int):
        """
            Initializes the class with the ticker list, a year and a month.

            The year and month are used to set the context of the analysis,
            meaning that financial data will be used for that year/month. 
            This is done to allow the analysis to be run in the past and test the
            quality of the results.


            Parameters
            ------------
            ticker_list : list of tickers to be included in the analisys
            year : analysis year
            month : analysis month
            portfolio_size : number of recommended securities that will be returned
                by this strategy

        """

        if (ticker_list is None or len(ticker_list) == 0):
            raise ValidationError("No ticker list was supplied", None)

        if  len(ticker_list) < 2:
            raise ValidationError("You must supply at least 2 ticker symbols", None)

        (self.analysis_start_date, self.analysis_end_date) = intrinio_util.get_month_date_range(data_year, data_month)

        
        if (self.analysis_end_date > datetime.now()):
            logging.debug("Setting analysis end date to 'today'")
            self.analysis_end_date = datetime.now()

        self.ticker_list = ticker_list

        self.portfolio_size = portfolio_size
        self.data_date = "%d-%d" % (data_year, data_month)

    def __load_financial_data__(self):
        """
            loads financial data into a map that is suitable to be converted
            into a pandas data frame

            pricing_raw_data = {
                'ticker': [],
                'target_price_avg': [],
                'target_price_sdtdev': [],
                'dispersion_stdev_pct': []
            }

            
            Raises
            ------------
            DataError in case financial data could not be loaed for any
            securities
        """

        logging.debug("Loading financial data for %s strategy" % self.STRATEGY_NAME)

        pricing_raw_data = {
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

        logging.debug("Analysis date range is %s, %s" % (dds.strftime("%Y-%m-%d"), dde.strftime("%Y-%m-%d")))
        logging.debug("Analysis price date is %s" % (dde.strftime("%Y-%m-%d")))

        for ticker in self.ticker_list:
            try:
                target_price_sdtdev = intrinio_data.get_target_price_std_dev(ticker, dds, dde)[year][month]
                target_price_avg = intrinio_data.get_target_price_mean(ticker, dds, dde)[year][month]
                dispersion_stdev_pct = target_price_sdtdev / target_price_avg * 100

                analysis_price = intrinio_data.get_latest_close_price(ticker, dde, 5)[1]

                analyst_expected_return = (target_price_avg - analysis_price) / analysis_price

                pricing_raw_data['analysis_period'].append(self.data_date)
                pricing_raw_data['ticker'].append(ticker)
                pricing_raw_data['analysis_price'].append(analysis_price)
                pricing_raw_data['target_price_avg'].append(target_price_avg)
                pricing_raw_data['dispersion_stdev_pct'].append(dispersion_stdev_pct)
                pricing_raw_data['analyst_expected_return'].append(analyst_expected_return )

                at_least_one = True
            except BaseError as be:
                logging.debug("Could not read %s financial data, because: %s" % (ticker, str(be)))
            except Exception as e:
                raise DataError("Could not read %s financial data" % (ticker), e)

        if not at_least_one:
            raise DataError("Could not load financial data for any if the supplied tickers", None)
        
        return pricing_raw_data


    def __calc_return_factor__(self, price_from : float, price_to : float):
        """
            calculates the return as a factor give two prices
        """
        return (price_to - price_from) / price_from

        

    def __convert_to_data_frame__(self, pricing_raw_data : dict):
        """
            converts the supplied financial_data into a pandas data frame.

            Parameters
            ------------
            pricing_raw_data : JSON document (suitable for pandas)
            containin the raw financial data

        """
        raw_dataframe = pd.DataFrame(pricing_raw_data)
        pd.options.display.float_format = '{:.3f}'.format
        raw_dataframe['decile'] = pd.qcut(pricing_raw_data['dispersion_stdev_pct'], 10, labels=False, duplicates='drop')
        raw_dataframe =  raw_dataframe.sort_values(['decile', 'analyst_expected_return'], ascending = (False, False))
    
        selected_portfolio = raw_dataframe.head(self.portfolio_size).drop(['decile', 'target_price_avg', 'dispersion_stdev_pct', 'analyst_expected_return'], axis=1)

        return (selected_portfolio, raw_dataframe)

    def generate_recommendation(self):
        """
            Creates a recommended portfolio and returns it as a pandas data frame
            and with the following fields:

            'ticker',
            'analysis_price',
            'current_price',
            'actual_return'
            
            Returns
            ------------
            A pandas data frame containing the recommended portfolio
        """
        (self.recommendation_dataframe, self.raw_dataframe) = self.__convert_to_data_frame__(self.__load_financial_data__())

        priced_securities = {}
        for row in self.recommendation_dataframe.itertuples(index=False):
            priced_securities[row.ticker] = row.analysis_price

        sr = SecurityRecommendationSet(datetime.now(), self.analysis_start_date, self.analysis_end_date, self.analysis_end_date, 
            self.STRATEGY_NAME, "US Equities", priced_securities)

        return sr