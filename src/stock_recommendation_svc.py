"""stock_recommendation_svc.py

"""
import argparse
import logging
from datetime import datetime, timedelta
from support import util
from exception.exceptions import ValidationError
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies import calculator
from service_support import recommendation_svc
from model.ticker_file import TickerFile
from support import constants


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
log = logging.getLogger()

logging.getLogger('boto3').setLevel(logging.WARN)
logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('s3transfer').setLevel(logging.WARN)
logging.getLogger('urllib3').setLevel(logging.WARN)


def parse_params():
    """
        Parse command line parameters, performs validation 
        and returns a sanitized version of it.
        
        Returns
        ----------
        A tuple containing the application paramter values
        (environment, ticker_file_name, portfolio_size, month, year, current_price_date, app_ns)
    """

    description = """ Reads a list of US Equity ticker symbols and recommends a subset of them
                  based on the degree of analyst target price agreement,
                  specifically it will select stocks with the lowest agreement and highest 
                  predicted return.

                  The input parameters are a file containing a list of of ticker symbols, 
                  the month and year period for the recommendations, a current price date used to compute
                  actual returns, and size of the final recommendation. The output is a JSON data 
                  structure with the final selection.

                  When running this script in "production" mode, the analysis period
                  is determined at runtime, and inputs, like the ticker file are downloaded
                  from S3.

              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-ticker_file", help="Ticker Symbol local file path", type=str, required=True)
    parser.add_argument("-portfolio_size", help="Selected Portfolio Size", type=int, required=True)

    subparsers = parser.add_subparsers(title='environment', 
        description='runtime environment', 
        dest="environment",
        help='the runtime environment of the application. It can be either "test" or "production"',
        required=True)

    test_subparser = subparsers.add_parser('test', help='Test mode. Analysis period and current date must be passed explicitly')
    test_subparser.add_argument("-analysis_month", help="Analysis period's month", type=int, required=True)
    test_subparser.add_argument("-analysis_year", help="Analysis period's year", type=int, required=True)
    test_subparser.add_argument("-price_date", help="Current Price Date (YYYY/MM/DD)", type=str, required=True)

    production_subparser = subparsers.add_parser('production', help='Production mode. Analysis period and current date are determined at runtime')
    production_subparser.add_argument("-app_namespace", help="Application namespace used to identify AWS resources", type=str, required=True)

    args = parser.parse_args()

    ticker_file_name = args.ticker_file
    portfolio_size = args.portfolio_size
    environment = args.environment
    app_ns = None

    # argparse will ensure that these will be set to the allowed values
    if (environment == 'test'):
        year = args.analysis_year
        month = args.analysis_month
        current_price_date = recommendation_svc.from_yyyymmdd(args.price_date)

        recommendation_svc.validate_commandline_parameters(
            year, month, current_price_date
        )
    else:
        current_price_date = datetime.now()
        (year, month) = recommendation_svc.compute_analysis_period(current_price_date)
        app_ns = args.app_namespace
    
    return (environment, ticker_file_name, portfolio_size, month, year, current_price_date, app_ns)


#
# Main script
#

try:
    (environment, ticker_file_name, portfolio_size, month, year, current_price_date, app_ns) = parse_params()

    log.info("Parameters:")
    log.info("Environment: %s" % environment)
    log.info("Ticker File: %s" % ticker_file_name)
    log.info("portfolio size: %d" % portfolio_size)
    log.info("month: %d" % month)
    log.info("year: %d" % year)
    log.info("current price date: %s" % datetime.strftime(current_price_date, '%Y/%m/%d'))
    
    
    if (environment == "test"):
        log.info("reading ticker file from local filesystem")
        ticker_list = TickerFile.from_local_file(constants.ticker_data_dir, ticker_file_name).ticker_list
    else:
        log.info("reading ticker file from local s3 bucket")
        ticker_list = TickerFile.from_s3_bucket(ticker_file_name, app_ns).ticker_list
    

    strategy = PriceDispersionStrategy(ticker_list, year, month, portfolio_size)
    
    log.info("Performing Ranking of securities")
    portfolio = strategy.generate_portfolio()
    portfolio_dataframe = strategy.portfolio_dataframe
    raw_dataframe = strategy.raw_dataframe

    log.info("Pricing securies")
    raw_dataframe = calculator.mark_to_market(strategy.raw_dataframe, current_price_date)
    portfolio_dataframe = calculator.mark_to_market(strategy.portfolio_dataframe, current_price_date)

    log.info("")
    log.info("Recommended Portfolio")
    log.info(util.format_dict(portfolio.to_dict()))
    log.info("")

    log.info("Recommended Portfolio Return: %.2f%%" % (portfolio_dataframe['actual_return'].mean()*100))
    log.info("Average Return: %.2f%%" % (raw_dataframe['actual_return'].mean()*100))
    log.info("")
    log.info("Analysis Period - %d/%d, Actual Returns as of: %s" % (month, year, datetime.strftime(current_price_date, '%Y/%m/%d')))

    print(raw_dataframe[['analysis_period', 'ticker', 'dispersion_stdev_pct', 'analyst_expected_return', 'actual_return', 'decile']].to_string(index=False))

except Exception as e:
    log.error("Could run script, because: %s" % (str(e)))
    exit(-1)

