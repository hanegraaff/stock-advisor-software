"""valuate_security.py

"""
import argparse
import logging
from support import util
from exception.exceptions import BaseError
from data_provider import intrinio_data
from support.financial_cache import cache
from strategies.low_price_dispersion_strategy import LowPriceDispersionStrategy
#
# Main script
#

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

description = """ Generate a portfolio reccomendation based given a list a ticker symbols.
                  Selection is based on on the degree of analyst target price agreement,
                  specifically it will select stocks with the lowest target price dispersion
                  and highest analyst predicted return.

                  The input parameter is a file containing a list of of ticker symbols (one per line), a 
                  current or historical month/year date context for this analysis, and a portfolio size 
                  indicating the number of recommended stocks.

                  The output is a table sorted into deciles that includes various target price statistics.
              """


parser = argparse.ArgumentParser(description=description)
parser.add_argument("-ticker-file", help="Ticker Symbol file", type=str)
parser.add_argument("-month", help="Data month", type=int)
parser.add_argument("-year", help="Data year", type=int)
parser.add_argument("-portfolio_size", help="Portfolio Size", type=int)

log = logging.getLogger()

args = parser.parse_args()

ticker_file = args.ticker_file
month = args.month
year = args.year
portfolio_size = args.portfolio_size

if (ticker_file == None or month == None or year == None or portfolio_size == None):
    log.error("Invalid Parameters: %s" % args)
    exit(-1)

if (year < 2000 or (month not in range(1, 13))):
    log.error("parameters out of range")
    exit(-1)


log.debug("Parameters:")
log.debug("Ticker File: %s" % ticker_file)
log.debug("month: %d" % month)
log.debug("year: %d" % year)
log.debug("portfolio size: %d" % portfolio_size)

ticker_list = []

try:
    with open(ticker_file) as f:
        ticker_list = f.read().splitlines()

    strategy = LowPriceDispersionStrategy(ticker_list, year, month, portfolio_size)
    portfolio = strategy.generate_portfolio()
    portfolio_dataframe = strategy.portfolio_dataframe
    raw_dataframe = strategy.raw_dataframe

    log.info("")
    log.info("Recommended Portfolio")
    log.info(util.format_dict(portfolio.to_dict()))
    log.info("")

    log.info("Recommended Portfolio Return: %.2f%%" % (portfolio_dataframe['actual_return'].mean()*100))
    log.info("Average Return: %.2f%%" % (strategy.raw_dataframe['actual_return'].mean()*100))
    log.info("")
    log.info("Analysis data")
    log.info(strategy.raw_dataframe)

    
except Exception as e:
    log.error("Could run script, because, %s" % (str(e)))
    exit(-1)
finally:
    # close the financial cache
    cache.close()
