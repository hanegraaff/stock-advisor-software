import intrinio_sdk
from intrinio_sdk.rest import ApiException
import os
from exception.exceptions import DataError, ValidationError
from data_provider import intrinio_util
from support.financial_cache import cache
import logging
import datetime
from datetime import timedelta

"""
This module is a value add to the Intrinio SDK
and implements a number of functions to read current and historical
financial statements
"""

API_KEY = os.environ['INTRINIO_API_KEY']

intrinio_sdk.ApiClient().configuration.api_key['api_key'] = API_KEY

fundamentals_api = intrinio_sdk.FundamentalsApi()
company_api = intrinio_sdk.CompanyApi()
security_api = intrinio_sdk.SecurityApi()


INTRINIO_CACHE_PREFIX = 'intrinio'


def get_target_price_std_dev(ticker : str, start_date : datetime, end_date : datetime):
    return _aggregate_by_year_month(
        _get_company_historical_data(ticker, intrinio_util.date_to_string(start_date), intrinio_util.date_to_string(end_date), 'zacks_target_price_std_dev')
    )

def get_target_price_mean(ticker : str, start_date : datetime, end_date : datetime):
    return _aggregate_by_year_month(
        _get_company_historical_data(ticker, intrinio_util.date_to_string(start_date), intrinio_util.date_to_string(end_date), 'zacks_target_price_mean')
    )

def get_target_price_cnt(ticker : str, start_date : datetime, end_date : datetime):
    return _aggregate_by_year_month(
        _get_company_historical_data(ticker, intrinio_util.date_to_string(start_date), intrinio_util.date_to_string(end_date), 'zacks_target_price_cnt')
    )


def get_daily_stock_close_prices(ticker : str, start_date : datetime, end_date : datetime):
      '''
        Returns a list of historical daily stock prices given a ticker symbol and
        a range of dates.

        Currently only returns one page of 100 results

        Parameters
        ----------
        ticker : str
          Ticker Symbol
        start_date : object
          The beginning price date as python date object
        end_date : object
          The end price date as python date object
        
        Raises
        -----------
        ValidationError in case of invalid paramters
        DataError in case of any Intrinio errors

        Returns
        -----------
        a dictionary of date->price like this
        {
          '2019-10-01': 100,
          '2019-10-02': 101,
          '2019-10-03': 102,
          '2019-10-04': 103,
        }
      '''

      start_date_str = intrinio_util.date_to_string(start_date)
      end_date_str = intrinio_util.date_to_string(end_date)

      price_dict = {}

      cache_key = "%s-%s-%s-%s-%s" % (INTRINIO_CACHE_PREFIX, ticker, start_date_str, end_date_str, "closing-prices")
      api_response = cache.read(cache_key)

      if api_response == None:
        try:
          api_response = security_api.get_security_stock_prices(ticker, start_date=start_date_str, end_date=end_date_str, frequency='daily', page_size=100)
          cache.write(cache_key, api_response)
        except ApiException as ae:
          raise DataError("API Error while reading price data from Intrinio Security API: ('%s', %s - %s)" %
                          (ticker, start_date_str, end_date_str), ae)
        except Exception as e:
          raise ValidationError("Unknown Error while reading price data from Intrinio Security API: ('%s', %s - %s)" %
                          (ticker, start_date_str, end_date_str), e)

      price_list = api_response.stock_prices

      if len(price_list) == 0:
        raise DataError("No prices returned from Intrinio Security API: ('%s', %s - %s)" %
                    (ticker, start_date_str, end_date_str), None)

      for price in price_list:  
        price_dict[intrinio_util.date_to_string(price.date)] = price.close

      return price_dict

def get_latest_close_price(ticker, price_date : datetime, max_looback : int):
    """
      Retrieves the most recent close price given a price_date and a lookback window

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      price_date : datetime
        pice date to look up
      max_looback : int
        maximum number of lookback days

      Raises
      -----------
      DataError in case a price could not be found

      Returns
      -----------
      a tuple of date, float with the latest price date and price value
    """

    if max_looback not in range (1,10):
      raise ValidationError("Invalid 'max_looback'. Allowed values are [1..10]", None)

    looback_date = price_date - timedelta(days=max_looback)

    price_dict = get_daily_stock_close_prices(ticker, looback_date, price_date)

    price_date = sorted(list(price_dict.keys()), reverse=True)[0]    
    
    return (price_date, price_dict[price_date])


def get_historical_revenue(ticker: str, year_from: int, year_to: int):
    '''
      Returns a dictionary of year->"total revenue" for the supplied ticker and 
      range of years.

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      year_from : int
        The beginning year to look up
      end_from : int
        The end year to look up

      Raises
      -----------
      ValidationError in case of invalid paramters
      DataError in case of any Intrinio errors

      Returns
      -----------
      a dictionary of year->"fcff value" like this
      {
        2010: 123,
        2012: 234,
        2013: 345,
        2014: 456,
      }
    '''

    start_date = intrinio_util.get_year_date_range(year_from, 0)[0]
    end_date = intrinio_util.get_year_date_range(year_to, 0)[1]

    return _aggregate_by_year(
        _get_company_historical_data(ticker, start_date, end_date, 'totalrevenue')
    )


def get_historical_fcff(ticker: str, year_from: int, year_to: int):
    '''
      Returns a dictionary of year->"fcff value" for the supplied ticker and 
      range of years.

        This is the description from Intrinio documentation:

        Definition
        Free cash flow for the firm (FCFF) is a measure of financial performance that 
        expresses the net amount of cash that is generated for a firm after expenses, 
        taxes and changes in net working capital and investments are deducted. 
        FCFF is essentially a measurement of a company's profitability after all expenses 
        and reinvestments. It's one of the many benchmarks used to compare and analyze 
        financial health.

        Formula
        freecashflow = nopat - investedcapitalincreasedecrease


      Parameters
      ----------
      ticker : str
        Ticker Symbol
      year_from : int
        The beginning year to look up
      end_from : int
        The end year to look up

      Raises
      -----------
      ValidationError in case of invalid paramters
      DataError in case of any Intrinio errors

      Returns
      -----------
      a dictionary of year->"fcff value" like this
      {
        2010: 123,
        2012: 234,
        2013: 345,
        2014: 456,
      }
    '''

    start_date = intrinio_util.get_year_date_range(year_from, 0)[0]
    end_date = intrinio_util.get_year_date_range(year_to, 0)[1]


    return _aggregate_by_year(
        _get_company_historical_data(ticker, start_date, end_date, 'freecashflow')
    )


def get_historical_income_stmt(ticker: str, year_from: int,
                               year_to: int, tag_filter_list: list):
    """
      returns a dictionary containing partial or complete income statements given
      a ticker symbol, year from, year to and a list of tag filters
      used to narrow the results.

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      year_from : int
        Start year of financial statement list
      year_to : int
        End year of the financial statement list 
      tag_filter_list : list
        List of data tags used to filter results. The name of each tag
        must match an expected one from the Intrinio API

      Returns
      -------
      A dictionary of year=>dict with the filtered results. For example:

      {2010: {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      },}

    """

    return _read_historical_financial_statement(
        ticker.upper(), 'income_statement', year_from, year_to, tag_filter_list)


def get_historical_balance_sheet(ticker: str, year_from: int,
                                 year_to: int, tag_filter_list: list):
    """
      returns a dictionary containing partial or complete balance sheets given
      a ticker symbol, year from, year to and a list of tag filters
      used to narrow the results.

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      year_from : int
        Start year of financial statement list
      year_to : int
        End year of the financial statement list 
      tag_filter_list : list
        List of data tags used to filter results. The name of each tag
        must match an expected one from the Intrinio API

      Returns
      -------
      A dictionary of year=>dict with the filtered results. For example:

      {2010: {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      },}

    """
    return _read_historical_financial_statement(
        ticker.upper(), 'balance_sheet_statement', year_from, year_to, tag_filter_list)


def get_historical_cashflow_stmt(ticker: str, year_from: int,
                                 year_to: int, tag_filter_list: list):
    """
      returns a partial or complete set of cashflow statements given
      a ticker symbol, year from, year to and a list of tag filters
      used to narrow the results.

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      year_from : int
        Start year of financial statement list
      year_to : int
        End year of the financial statement list 
      tag_filter_list : list
        List of data tags used to filter results. The name of each tag
        must match an expected one from the Intrinio API

      Returns
      -------
      A dictionary of year=>dict with the filtered results. For example:

      {2010: {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      },}

    """
    return _read_historical_financial_statement(
        ticker.upper(), 'cash_flow_statement', year_from, year_to, tag_filter_list)


#
# Private Helper methods
#

def _transform_financial_stmt(std_financials_list: list, tag_filter_list: list):
    """
      Helper function that transforms a financial statement stored in
      the raw Intrinio format into a more user friendly one.


      Parameters
      ----------
      std_financials_list : list
        List of standardized financials extracted from the Intrinio API
      tag_filter_list : list
        List of data tags used to filter results. The name of each tag
        must match an expected one from the Intrinio API

      Returns
      -------
      A dictionary of tag=>value with the filtered results. For example:

      {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      }

      Note that the name of the tags are specific to the Intrinio API
    """
    results = {}

    for financial in std_financials_list:

        if (tag_filter_list == None or
                financial.data_tag.tag in tag_filter_list):
            results[financial.data_tag.tag] = financial.value

    return results


def _read_historical_financial_statement(ticker: str, statement_name: str, year_from: int, year_to: int, tag_filter_list: list):
    """
      This helper function will read standardized fiscal year end financials from the Intrinio fundamentals API
      for each year in the supplied range, and normalize the results into simpler user friendly
      dictionary, for example:

      {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      }

      results may also be filtered based on the tag_filter_list parameter, which may include
      just the tags that should be returned.

      Parameters
      ----------
      ticker : str
        Ticker Symbol
      statement_name : str
        The name of the statement to read.
      year_from : int
        Start year of financial statement list
      year_to : int
        End year of the financial statement list 
      tag_filter_list : list
        List of data tags used to filter results. The name of each tag
        must match an expected one from the Intrinio API. If "None", then all
        tags will be returned.

      Raises
      -------
      DataError in case of any error calling the intrio API

      Returns
      -------
      A dictionary of tag=>value with the filtered results. For example:

      {
        'netcashfromcontinuingoperatingactivities': 77434000000.0,
        'purchaseofplantpropertyandequipment': -13313000000
      }

      Note that the name of the tags are specific to the Intrinio API

    """
    # return value
    hist_statements = {}
    ticker = ticker.upper()

    statement_type = 'FY'

    try:
      for i in range(year_from, year_to + 1):
          satement_name = ticker + "-" + \
              statement_name + "-" + str(i) + "-" + statement_type

          cache_key = "%s-%s-%s-%s-%s-%d" % (INTRINIO_CACHE_PREFIX, "statement", ticker, statement_name, statement_type, i)
          statement = cache.read(cache_key)

          if statement == None:
            statement = fundamentals_api.get_fundamental_standardized_financials(
                satement_name)

            cache.write(cache_key, statement)

          hist_statements[i] = _transform_financial_stmt(
              statement.standardized_financials, tag_filter_list)

    except ApiException as ae:
        raise DataError(
            "Error retrieving ('%s', %d - %d) -> '%s' from Intrinio Fundamentals API" % (ticker, year_from, year_to, statement_name), ae)

    return hist_statements


def _read_company_data_point(ticker: str, tag: str):
    """
      Helper function that will read the Intrinio company API for the supplied ticker
      and return the value


      Returns
      -------
      The numerical value of the datapoint
    """


    # check the cache first
    cache_key = "%s-%s-%s-%s" % (INTRINIO_CACHE_PREFIX, "company_data_point_number", ticker, tag)
    api_response = cache.read(cache_key)

    if api_response == None:
      # else call the API directly
      try:
          api_response = company_api.get_company_data_point_number(
              ticker, tag)

          cache.write(cache_key, api_response)
      except ApiException as ae:
          raise DataError(
              "Error retrieving ('%s') -> '%s' from Intrinio Company API" % (ticker, tag), ae)
      except Exception as e:
          raise ValidationError(
              "Error parsing ('%s') -> '%s' from Intrinio Company API" % (ticker, tag), e)

    return api_response


def _get_company_historical_data(ticker: str, start_date: str, end_date: str, tag: str):
    """
      Helper function that will read the Intrinio company API for the supplied date range

      Parameters
      ----------
      ticker : str
        Ticker symbol. E.g. 'AAPL'
      start_date : str
        Start date of the metric formatted as YYYY-MM-DD
      end_date : str
        End date of the metric formatted as YYYY-MM-DD
      tag : the metric name to retrieve

      Raises
      -------
      DataError in case of any error calling the intrio API
      ValidationError in case of an unknown exception

      Returns
      -------
      The 'historical_data_dict' portion of the 'get_company_historical_data'

      [
        {'date': datetime.date(2018, 9, 29), 'value': 265595000000.0},
        {'date': datetime.date(2017, 9, 30), 'value': 229234000000.0}
      ]
    """

    frequency = 'yearly'
    
    # check the cache first
    cache_key = "%s-%s-%s-%s-%s-%s-%s" % (INTRINIO_CACHE_PREFIX, "company_historical_data", ticker, start_date, end_date, frequency, tag)
    api_response = cache.read(cache_key)

    if api_response == None:
      # else call the API directly
      try:
          api_response = company_api.get_company_historical_data(
              ticker, tag, frequency=frequency, start_date=start_date, end_date=end_date)
      except ApiException as ae:
          raise DataError(
              "Error retrieving ('%s', %s - %s) -> '%s' from Intrinio Company API" % (ticker, start_date, end_date, tag), ae)
      except Exception as e:
          raise ValidationError(
              "Error parsing ('%s', %s - %s) -> '%s' from Intrinio Company API" % (ticker, start_date, end_date, tag), e)

    if len(api_response.historical_data) == 0:
        raise DataError("No Data returned for ('%s', %s - %s) -> '%s' from Intrinio Company API" %
                        (ticker, start_date, end_date, tag), None)
    else:
        #only write to cache if response has some valid data
        cache.write(cache_key, api_response)

    return api_response.historical_data_dict

def _aggregate_by_year(historical_data_dict : dict):
    """
      Map historical company data by year (latest occurrence).

      Input

      [
        {'date': datetime.date(2018, 9, 29), 'value': 123.0},
        {'date': datetime.date(2017, 9, 30), 'value': 234.0}
      ]

      Output

      {
        2018: 123,
        2019: 234
      }
      

      Parameters
      ----------
      api_response : dict
        get_company_historical_data API response

      Returns
      -------
      A dictionary of year=>value with the converted results.
    """

    converted_response = {}

    for datapoint in historical_data_dict:
        converted_response[datapoint['date'].year] = datapoint['value']

    return converted_response


def _aggregate_by_year_month(historical_data : dict):
    """
      Map historical company data by year and month and average out results.

      Input

      [
        {'date': datetime.date(2019, 9, 1), 'value': 10},
        {'date': datetime.date(2019, 9, 15), 'value': 20},
        {'date': datetime.date(2019, 10, 12), 'value': 30}
      ]

      Output

      {
        2019: {
          9 : 15,
          10 : 30
        } 
      }
      

      Parameters
      ----------
      api_response : dict
        get_company_historical_data API response

      Returns
      -------
      A dictionary of year=>month=>value with the converted results.
    """
    if historical_data is None: return {}

    converted_response = {}

    # first pass assemble the basic return value
    for datapoint in historical_data:
      year = datapoint['date'].year
      month = datapoint['date'].month

      if year not in converted_response:
        converted_response[year] = {}
      if month not in converted_response[year]:
        converted_response[year][month] = []

      converted_response[year][month].append(datapoint['value'])

    # second pass calculate averages
    for year in converted_response.keys():
      for month in converted_response[year]:
        converted_response[year][month] = sum(converted_response[year][month]) / len(converted_response[year][month])
          
    
    return converted_response




