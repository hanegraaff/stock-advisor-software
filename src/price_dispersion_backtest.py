"""price_dispersion_backtest.py
"""
import argparse
import logging
import pandas as pd
import pandas_market_calendars as mcal
from datetime import date
from datetime import timedelta
from support import util
from connectors import intrinio_util
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies import calculator
from model.ticker_list import TickerList
from support import constants, logging_definition

log = logging.getLogger()


def get_nearest_business_date(cal_date: date):
    '''
        given a calendar date, returns the nearest past business date
    '''
    nyse_cal = mcal.get_calendar('NYSE')

    market_calendar = nyse_cal.schedule(
        cal_date - timedelta(days=5), cal_date + timedelta(days=5))

    business_date_index = market_calendar.index.get_loc(
        str(cal_date), method='ffill')

    business_date = market_calendar.iloc[
        business_date_index].market_close.to_pydatetime().date()

    return business_date


def main():
    """
        Main Function for this script
    """

    description = """
                Backtest script for the PRICE_DISPERSION strategy.

                This script will execute the strategy for each month of available data,
                and compare the returns of the selected portfolio with the average of the 
                supplied ticker list.
                The script will show returns of a 1 month, 2 month and three month horizon
                displayed as a Pandad Dataframe

              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-ticker_list", help="Ticker Symbol File",
                        type=str, required=True)
    parser.add_argument(
        "-output_size", help="Number of selected securities", type=int, required=True)

    args = parser.parse_args()

    ticker_file_name = args.ticker_list
    output_size = args.output_size

    log.info("Parameters:")
    log.info("Ticker File: %s" % ticker_file_name)
    log.info("Output Size: %d" % output_size)

    ticker_list = None

    backtest_report = {
        'investment_period': [],
        'ticker_sample_size': [],
        'avg_ret_1M': [],
        'sel_ret_1M': [],
        'avg_ret_2M': [],
        'sel_ret_2M': [],
        'avg_ret_3M': [],
        'sel_ret_3M': []
    }

    backtest_summary = {
        'investment_period': [],
        'ticker_sample_size': [],
        'avg_tot_1M': [],
        'sel_tot_1M': [],
        'avg_tot_2M': [],
        'sel_tot_2M': [],
        'avg_tot_3M': [],
        'sel_tot_3M': []
    }

    today = date.today()

    def backtest(analysis_period: str):
        log.info("Performing backtest for %s" % analysis_period)

        period = pd.Period(analysis_period)

        data_end_date = intrinio_util.get_month_period_range(period)[1]

        strategy = PriceDispersionStrategy(
            ticker_list, period, None, output_size)
        strategy.generate_recommendation()

        date_1m = get_nearest_business_date(data_end_date + timedelta(days=30))
        date_2m = get_nearest_business_date(data_end_date + timedelta(days=60))
        date_3m = get_nearest_business_date(data_end_date + timedelta(days=90))

        portfolio_1m = calculator.mark_to_market(
            strategy.recommendation_dataframe, 'ticker', 'analysis_price', date_1m)['actual_return'].mean() * 100
        portfolio_2m = calculator.mark_to_market(
            strategy.recommendation_dataframe, 'ticker', 'analysis_price', date_2m)['actual_return'].mean() * 100
        portfolio_3m = calculator.mark_to_market(
            strategy.recommendation_dataframe, 'ticker', 'analysis_price', date_3m)['actual_return'].mean() * 100

        all_stocks_1m = calculator.mark_to_market(strategy.raw_dataframe, 'ticker', 'analysis_price', date_1m)[
            'actual_return'].mean() * 100
        all_stocks_2m = calculator.mark_to_market(strategy.raw_dataframe, 'ticker', 'analysis_price', date_2m)[
            'actual_return'].mean() * 100
        all_stocks_3m = calculator.mark_to_market(strategy.raw_dataframe, 'ticker', 'analysis_price', date_3m)[
            'actual_return'].mean() * 100

        backtest_report['investment_period'].append(
            data_end_date.strftime('%Y/%m'))
        backtest_report['ticker_sample_size'].append(
            len(strategy.raw_dataframe))

        backtest_report['avg_ret_1M'].append(all_stocks_1m)
        backtest_report['sel_ret_1M'].append(portfolio_1m)
        backtest_report['avg_ret_2M'].append(all_stocks_2m)
        backtest_report['sel_ret_2M'].append(portfolio_2m)
        backtest_report['avg_ret_3M'].append(all_stocks_3m)
        backtest_report['sel_ret_3M'].append(portfolio_3m)

    try:

        ticker_list = TickerList.from_local_file("%s/%s" %
                                                 (constants.TICKER_DATA_DIR, ticker_file_name))

        backtest('2019-05')
        backtest('2019-06')
        backtest('2019-07')
        backtest('2019-08')
        backtest('2019-09')
        backtest('2019-10')
        backtest('2019-11')
        backtest('2019-12')
        backtest('2020-01')
        backtest('2020-02')

        backtest_dataframe = pd.DataFrame(backtest_report)
        pd.options.display.float_format = '{:.2f}%'.format
        print(backtest_dataframe.to_string(index=False))

        backtest_summary['investment_period'] = ['----/--']
        backtest_summary['ticker_sample_size'] = ['--']

        backtest_summary['avg_tot_1M'].append(
            backtest_dataframe['avg_ret_1M'].sum())
        backtest_summary['sel_tot_1M'].append(
            backtest_dataframe['sel_ret_1M'].sum())
        backtest_summary['avg_tot_2M'].append(
            backtest_dataframe['avg_ret_2M'].sum())
        backtest_summary['sel_tot_2M'].append(
            backtest_dataframe['sel_ret_2M'].sum())
        backtest_summary['avg_tot_3M'].append(
            backtest_dataframe['avg_ret_3M'].sum())
        backtest_summary['sel_tot_3M'].append(
            backtest_dataframe['sel_ret_3M'].sum())

        backtest_summary_dataframe = pd.DataFrame(backtest_summary)
        print(backtest_summary_dataframe.to_string(index=False))

    except Exception as e:
        log.error("Could run script, because, %s" % (str(e)))
        raise e
        exit(-1)

if __name__ == "__main__":
    main()
