"""macd_crossover_backtest.py
"""
import argparse
import pandas as pd
import logging
import pandas_market_calendars as mcal
from datetime import date, datetime
from connectors import intrinio_data
from strategies.macd_crossover_strategy import MACDCrossoverStrategy
from model.ticker_list import TickerList
from support import constants, logging_definition
from exception.exceptions import ValidationError

log = logging.getLogger()

pd.set_option("display.max_rows", None, "display.max_columns", None)
pd.options.display.float_format = '{:.2f}'.format

'''
    A dictionary of existing positions
    {
        'AAPL': (buy_date, buy_price)
    }
'''
POSITIONS_DICT = {}

# MACD Parameters
DIVERGENCE_FACTOR_THRESHOLD = 0.0016
FAST_PERIOD = 12
SLOW_PERIOD = 26
SIGNAL_PERIOD = 9


def main():
    """
        Main Function for this script
    """

    description = """
                Executes a backtest for the MACD_CROSSOVER strategy given a ticker list,
                start date, end date and threshold, e.g. -0.02, used to determine the maximum
                allowed loss of a trade before a stop loss takes effect.
              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-ticker_list", help="Ticker List File",
                        type=str, required=True)
    date_parser = lambda s: datetime.strptime(s, '%Y/%m/%d')
    parser.add_argument("-start_date", help="Backtest start date (YYY/MM/DD)",
                        type=date_parser, required=True)
    parser.add_argument("-end_date", help="Backtest end date (YYYY/MM/DD)",
                        type=date_parser, required=True)
    parser.add_argument("-stop_loss_theshold", help="Stop Loss Threshold factor, e.g. -0.02 (-2%%)",
                        type=float, required=True)

    args = parser.parse_args()

    ticker_file_name = args.ticker_list
    start_date = args.start_date
    end_date = args.end_date
    stop_loss_theshold = args.stop_loss_theshold

    log.info("Parameters:")
    log.info("Ticker File: %s" % ticker_file_name)
    log.info("Start Date: %s" % start_date)
    log.info("End Date: %s" % end_date)
    log.info("Stop Loss Threshold: %.2f" % stop_loss_theshold)

    log.info("")
    log.info("MACD Configuration:")
    log.info("Divergence Tolerance Factor: %f" % DIVERGENCE_FACTOR_THRESHOLD)
    log.info("Slow Period: %d" % SLOW_PERIOD)
    log.info("Fast Period: %d" % FAST_PERIOD)
    log.info("Signal Period: %d" % SIGNAL_PERIOD)

    log.info("")

    ticker_list = TickerList.from_local_file("%s/%s" %
                                             (constants.TICKER_DATA_DIR, ticker_file_name))

    trade_dict = {
        'ticker': [],
        'buy_date': [],
        'buy_price': [],
        'sell_date': [],
        'sell_price': [],
        'trade_pnl_factor': [],
        'false_signal': []
    }

    try:
        date_list = get_business_date_list(start_date, end_date)
        init_portfolio_dict(ticker_list)

        for i in range(0, len(date_list) - 1):
            recommendation_date = date_list[i]
            trade_date = date_list[i + 1]

            strategy = MACDCrossoverStrategy(
                ticker_list, recommendation_date, DIVERGENCE_FACTOR_THRESHOLD, FAST_PERIOD, SLOW_PERIOD, SIGNAL_PERIOD)
            strategy.generate_recommendation()

            print("processing: %s" % recommendation_date, end="\r")

            unwound_positions = trade(
                trade_date, strategy.recommendation_set)

            for position in unwound_positions:
                (ticker, buy_date, sell_date, buy_price) = position

                sell_price = get_close_price(ticker, sell_date)
                pnl = ((sell_price / buy_price) - 1)
                false_signal = 0

                if (pnl < stop_loss_theshold):
                    sell_price = 'STOP_LOSS'
                    false_signal = 1
                    pnl = stop_loss_theshold

                if (pnl < 0):
                    false_signal = 1

                trade_dict['ticker'].append(ticker)
                trade_dict['buy_date'].append(buy_date)
                trade_dict['buy_price'].append(buy_price)
                trade_dict['sell_date'].append(str(sell_date))
                trade_dict['sell_price'].append(sell_price)
                trade_dict['trade_pnl_factor'].append(pnl)
                trade_dict['false_signal'].append(false_signal)

        trades_by_ticker = []
        for ticker in ticker_list.model['ticker_symbols']:
            trades_by_ticker.append(calculate_returns(ticker, trade_dict))
        trade_dataframe = pd.concat(trades_by_ticker)

        display_results(trade_dataframe)

    except Exception as e:
        log.error("Could run script, because, %s" % (str(e)))
        raise e


def get_business_date_list(start_date: date, end_date: date):
    '''
        given a calendar date, returns the nearest past business date
    '''
    if start_date >= end_date:
        raise ValidationError("Start date must be before end date")

    nyse_cal = mcal.get_calendar('NYSE')

    market_calendar = nyse_cal.schedule(
        start_date, end_date)
    business_date_list = [date.date() for date in list(market_calendar.index)]
    return business_date_list


def get_close_price(ticker: str, price_date: date):
    '''
        Reads the close price of a ticker symbol given a price date
    '''
    return intrinio_data.get_daily_stock_close_prices(
        ticker, price_date, price_date
    )[str(price_date)]


def init_portfolio_dict(ticker_list: object):
    '''
        Initializes the portfolio dictionary based on the ticker list
    '''
    POSITIONS_DICT.clear()

    for ticker in ticker_list.model['ticker_symbols']:
        POSITIONS_DICT[ticker] = None


def trade(trade_date: date, recommendation_set: object):
    '''
        Executes a potential trade based on the contents of the recommednation set.
        Specifically, it will simulate the purchase of any recommeneded security
        and simulate the sale of any security that dropped off. 
    '''
    security_set = recommendation_set.model['securities_set']

    unwound_positions = []
    recommended_ticker_list = [ticker_dict['ticker_symbol']
                               for ticker_dict in security_set]

    # add positions based on new recommendations
    for ticker_dict in security_set:
        ticker = ticker_dict['ticker_symbol']
        if POSITIONS_DICT[ticker] == None:
            buy_price = get_close_price(ticker, trade_date)
            POSITIONS_DICT[ticker] = (trade_date, buy_price)

    # remove existing positions no longer recommended
    for ticker in POSITIONS_DICT.keys():
        if POSITIONS_DICT[ticker] is not None and ticker not in recommended_ticker_list:
            (buy_date, buy_price) = POSITIONS_DICT[ticker]
            unwound_positions.append((ticker, buy_date, trade_date, buy_price))
            POSITIONS_DICT[ticker] = None

    return unwound_positions


def calculate_returns(ticker: str, trade_dict: object):
    '''
        Returns an enriched Pandas Dataframe, based on the study's final trades,
        filtered by ticker symbol, and including the cumulative PNL expressed
        as a growth of 10K 
    '''
    trade_dataframe = pd.DataFrame(trade_dict)

    if len(trade_dataframe) == 0:
        return trade_dataframe

    trade_dataframe['10k_growth'] = 0
    trade_dataframe = trade_dataframe.loc[trade_dataframe['ticker'] == ticker].sort_values(
        ['sell_date'], ascending=(True)).reset_index(drop=True)

    return_amt = 10000
    for i in range(0, len(trade_dataframe)):
        trade_dataframe.loc[i, '10k_growth'] = return_amt + \
            (return_amt * trade_dataframe.loc[i, 'trade_pnl_factor'])
        return_amt = trade_dataframe.loc[i, '10k_growth']

    return trade_dataframe


def display_results(trade_dataframe: object):
    '''
        Display the results of the backtest study
    '''
    def xform_totals(ticker_df: object):
        xformed_dict = {}

        xformed_dict['Ticker'] = ticker_df.loc[0, 'ticker']
        xformed_dict['Compounded PNL (%)'] = (
            ticker_df.loc[len(ticker_df) - 1, '10k_growth'] - 10000) / 100
        xformed_dict['Average Trade PNL (%)'] = ticker_df[
            'trade_pnl_factor'].mean() * 100
        xformed_dict['False Signals (%)'] = ticker_df['false_signal'].sum(
        ) / ticker_df['false_signal'].count() * 100
        return pd.Series(xformed_dict)

    print("")
    if len(trade_dataframe) == 0:
        log.warning("No trades resulted from this backtest")
        return

    totals_dataframe = trade_dataframe \
        .groupby(['ticker']).apply(xform_totals).sort_values(['Compounded PNL (%)'], ascending=(False))
    print(totals_dataframe.to_string(index=False))

    print(trade_dataframe.drop(
        ['false_signal'], axis=1).to_string(index=False))


if __name__ == "__main__":
    main()
