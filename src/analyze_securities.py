"""valuate_security.py

"""
import argparse
import datetime
from datetime import timedelta
import logging
from support import util
from exception.exceptions import BaseError
from data_provider import intrinio_data
from support.financial_cache import cache
from support import util
#
# Main script
#

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

description = """ Analyzes securities and displays the degree price target consensus based on Zacks market data
                  provided by Intrinio.

                  The input parameters can either be a ticker symbol or a file containing a list of them.
                  The output is a dictionary printed to the console containing price target metrics.
              """


parser = argparse.ArgumentParser(description=description)
parser.add_argument("-ticker", help="Ticker Symbol", type=str)
parser.add_argument("-ticker-file", help="Ticker Symbol file", type=str)

log = logging.getLogger()

args = parser.parse_args()

ticker = args.ticker.upper() if args.ticker != None else None
ticker_file = args.ticker_file

if ((ticker == None and ticker_file == None) or (ticker != None and ticker_file != None)):
    print("Invalid Parameters. Must supply either 'ticker' or 'ticker-file' parameter")
    exit(-1)

log.debug("Parameters:")
log.debug("Ticker: %s" % ticker)
log.debug("Ticker File: %s" % ticker_file)

today = datetime.datetime.now()
five_days_ago = today - timedelta(days=5)

ticker_list = []

if (ticker != None):
    ticker_list.append(ticker)
else:
    try:
        with open(ticker_file) as f:
            ticker_list = f.read().splitlines()
    except Exception as e:
        logging.error("Could run script, because, %s" % (str(e)))
        exit(-1)

results = {}
for ticker in ticker_list:
    try:
        price_dict = intrinio_data.get_daily_stock_close_prices(
            ticker, five_days_ago, today)
        current_price = price_dict[sorted(
            list(price_dict.keys()), reverse=True)[0]]

        target_price_sdtdev = intrinio_data.__read_company_data_point__(ticker, 'zacks_target_price_std_dev')
        target_price_avg = intrinio_data.__read_company_data_point__(ticker, 'zacks_target_price_mean')
        target_price_sdtdev_pct = target_price_sdtdev / target_price_avg * 100

        analyst_dict = {
            'ticker' : ticker,
            'target_price_count' : intrinio_data.__read_company_data_point__(ticker, 'zacks_target_price_cnt'),
            'target_price_sdtdev' : target_price_sdtdev,
            'target_price_avg' : target_price_avg,
            'target_price_sdtdev_pct' : "%4.3f" % target_price_sdtdev_pct,
            'current_price' : current_price
        }

        results[target_price_sdtdev_pct] = analyst_dict

    except BaseError as be:
        logging.debug("Could not valuate %s, because: %s" % (ticker, str(be)))

    for key in sorted(list(results)):
        logging.info("%s" % util.format_dict(results[key]))

# close the financial cache
cache.close()
