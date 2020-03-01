"""valuate_security.py

"""
import argparse
import logging
from datetime import datetime
from support import util
from exception.exceptions import BaseError
from support.financial_cache import cache
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies import calculator

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
log = logging.getLogger()

def from_yyyymmdd(datestr):
  try:
    return datetime.strptime(datestr, '%Y/%m/%d')
  except Exception:
    log.error("%s is invalid. Expecting 'yyyy/mm/dd' format" % datestr)
    exit(-1)

#
# Main script
#


description = """ Generate a portfolio recommendation given a list of ticker symbols.
                  Selection is based on on the degree of analyst target price agreement,
                  specifically it will select stocks with the lowest agreement and highest 
                  predicted return.

                  The input parameters are a file containing a list of of ticker symbols, 
                  the period for the recommendations, a price date used to show actual returns 
                  and the size of the final portfolio selection.

                  The output is a data structure with the selection, and a data frame showing 
                  the underlining stock ranking.
              """


parser = argparse.ArgumentParser(description=description)
parser.add_argument("-ticker-file", help="Ticker Symbol file", type=str)
parser.add_argument("-analysis_month", help="Analysis period's month", type=int)
parser.add_argument("-analysis_year", help="Analysis period's year", type=int)
parser.add_argument("-price_date", help="Current Price Date (YYYY/MM/DD)", type=str)
parser.add_argument("-portfolio_size", help="Selected Portfolio Size", type=int)


args = parser.parse_args()

ticker_file = args.ticker_file
month = args.analysis_month
year = args.analysis_year
portfolio_size = args.portfolio_size

#
# Validate the supplied dates and ranges
#
current_price_date = from_yyyymmdd(args.price_date)
if current_price_date > datetime.now():
    log.error("Price Date cannot be in future")
    exit(-1)

if (year >= current_price_date.year and month >= current_price_date.month):
    log.error("Price Date must be in future compared to analysis period")
    exit(-1)


if (ticker_file == None or month == None or year == None or portfolio_size == None):
    log.error("Invalid parameters: %s" % args)
    exit(-1)

if (year < 2000 or (month not in range(1, 13))):
    log.error("Parameters out of range")
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

    strategy = PriceDispersionStrategy(ticker_list, year, month, portfolio_size)
    
    log.debug("Generating portfolio recommendation")

    portfolio = strategy.generate_portfolio()
    portfolio_dataframe = strategy.portfolio_dataframe
    raw_dataframe = strategy.raw_dataframe

    raw_dataframe = calculator.mark_to_market(strategy.raw_dataframe, current_price_date)
    portfolio_dataframe = calculator.mark_to_market(strategy.portfolio_dataframe, current_price_date)

    log.info("")
    log.info("Recommended Portfolio")
    log.info(util.format_dict(portfolio.to_dict()))
    log.info("")

    log.info("Recommended Portfolio Return: %.2f%%" % (portfolio_dataframe['actual_return'].mean()*100))
    log.info("Average Return: %.2f%%" % (raw_dataframe['actual_return'].mean()*100))
    log.info("")
    log.info("Analysis Period - %d/%d, Actual Returns as of: %s" % (month, year, args.price_date))

    print(raw_dataframe[['analysis_period', 'ticker', 'dispersion_stdev_pct', 'analyst_expected_return', 'actual_return', 'decile']].to_string(index=False))


    
except Exception as e:
    log.error("Could run script, because, %s" % (str(e)))
    exit(-1)
finally:
    # close the financial cache
    cache.close()
