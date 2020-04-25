"""price_dispersion_backtest.py
"""
import argparse
import logging
import pandas as pd
from datetime import datetime
from datetime import timedelta
from support import util
from exception.exceptions import BaseError
from data_provider import intrinio_util
from support.financial_cache import cache
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies import calculator
from model.ticker_file import TickerFile
from support import constants


#
# Main script
#

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

description = """ 
                A backtest for the PRICE_DISPERSION strategy

                It works by running the strategy on a monthly basis and then displaying
                the average current returns vs the selected portolio returns.

              """


parser = argparse.ArgumentParser(description=description)
parser.add_argument("-ticker_file", help="Ticker Symbol file", type=str, required=True)
parser.add_argument("-output_size", help="Number of selected securities", type=int, required=True)

log = logging.getLogger()

args = parser.parse_args()

ticker_file_name = args.ticker_file
output_size = args.output_size

log.info("Parameters:")
log.info("Ticker File: %s" % ticker_file_name)
log.info("Output Size: %d" % output_size)

ticker_list = []

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

today = datetime.now()

def backtest(year : int, month : int):
    data_end_date = intrinio_util.get_month_date_range(year, month)[1]

    strategy = PriceDispersionStrategy(ticker_list, year, month, output_size)
    strategy.generate_recommendation()

    date_1m = data_end_date + timedelta(days=30)
    date_2m = data_end_date + timedelta(days=60)
    date_3m = data_end_date + timedelta(days=90)

    portfolio_1m = calculator.mark_to_market(strategy.recommendation_dataframe, date_1m)['actual_return'].mean()*100
    portfolio_2m = calculator.mark_to_market(strategy.recommendation_dataframe, date_2m)['actual_return'].mean()*100
    portfolio_3m = calculator.mark_to_market(strategy.recommendation_dataframe, date_3m)['actual_return'].mean()*100

    all_stocks_1m = calculator.mark_to_market(strategy.raw_dataframe, date_1m)['actual_return'].mean()*100
    all_stocks_2m = calculator.mark_to_market(strategy.raw_dataframe, date_2m)['actual_return'].mean()*100
    all_stocks_3m = calculator.mark_to_market(strategy.raw_dataframe, date_3m)['actual_return'].mean()*100

    backtest_report['investment_period'].append(data_end_date.strftime('%Y/%m'))
    backtest_report['ticker_sample_size'].append(len(strategy.raw_dataframe))

    backtest_report['avg_ret_1M'].append(all_stocks_1m)
    backtest_report['sel_ret_1M'].append(portfolio_1m)
    backtest_report['avg_ret_2M'].append(all_stocks_2m)
    backtest_report['sel_ret_2M'].append(portfolio_2m)
    backtest_report['avg_ret_3M'].append(all_stocks_3m)
    backtest_report['sel_ret_3M'].append(portfolio_3m)

try:

    ticker_list = TickerFile.from_local_file(constants.TICKER_DATA_DIR, ticker_file_name).ticker_list

    backtest(2019, 5)
    backtest(2019, 6)
    backtest(2019, 7)
    backtest(2019, 8)
    backtest(2019, 9)
    backtest(2019, 10)
    backtest(2019, 11)
    backtest(2019, 12)
    #backtest(2020, 1)


    backtest_dataframe = pd.DataFrame(backtest_report)
    pd.options.display.float_format = '{:.2f}%'.format
    print(backtest_dataframe.to_string(index=False)) 


    backtest_summary['investment_period'] = ['----/--']
    backtest_summary['ticker_sample_size']= ['--']

    backtest_summary['avg_tot_1M'].append(backtest_dataframe['avg_ret_1M'].sum())
    backtest_summary['sel_tot_1M'].append(backtest_dataframe['sel_ret_1M'].sum())
    backtest_summary['avg_tot_2M'].append(backtest_dataframe['avg_ret_2M'].sum())
    backtest_summary['sel_tot_2M'].append(backtest_dataframe['sel_ret_2M'].sum())
    backtest_summary['avg_tot_3M'].append(backtest_dataframe['avg_ret_3M'].sum())
    backtest_summary['sel_tot_3M'].append(backtest_dataframe['sel_ret_3M'].sum())


    backtest_summary_dataframe = pd.DataFrame(backtest_summary)
    print(backtest_summary_dataframe.to_string(index=False)) 
    
except Exception as e:
    log.error("Could run script, because, %s" % (str(e)))
    exit(-1)
