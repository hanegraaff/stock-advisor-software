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
        (environment, ticker_file_name, output_size, month, year, current_price_date, app_ns)
    """

    description = """ Reads a list of US Equity ticker symbols and recommends a subset of them
                  based on the degree of analyst target price agreement,
                  specifically it will select stocks with the lowest agreement and highest 
                  predicted return.

                  The input parameters consist of a file with a list of of ticker symbols, 
                  and the month and year period for the recommendations. 
                  The output is a JSON data structure with the final selection.

                  When running this script in "production" mode, the analysis period
                  is determined at runtime, and the system wil plug into the AWS infrastructure
                  to read inputs and store outputs.
              """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-ticker_file", help="Ticker Symbol local file path", type=str, required=True)
    parser.add_argument("-output_size", help="Number of selected securities", type=int, required=True)

    subparsers = parser.add_subparsers(title='environment', 
        description='runtime environment', 
        dest="environment",
        help='the runtime environment of the application. It can be either "test" or "production"',
        required=True)

    test_subparser = subparsers.add_parser('test', help='Test mode. Analysis period and current date must be passed explicitly')
    test_subparser.add_argument("-analysis_month", help="Analysis period's month", type=int, required=True)
    test_subparser.add_argument("-analysis_year", help="Analysis period's year", type=int, required=True)
    test_subparser.add_argument("-price_date", help="Price Date (YYYY/MM/DD) used to compute current returns", type=str, required=False)

    production_subparser = subparsers.add_parser('production', help='Production mode. Analysis period and current date are determined at runtime')
    production_subparser.add_argument("-app_namespace", help="Application namespace used to identify AWS resources", type=str, required=True)

    args = parser.parse_args()

    ticker_file_name = args.ticker_file
    output_size = args.output_size
    environment = args.environment
    app_ns = None

    environment = recommendation_svc.validate_environment(environment)

    # argparse will ensure that these will be set to the allowed values
    if (environment == 'TEST'):
        year = args.analysis_year
        month = args.analysis_month
        price_date_string = args.price_date

        if price_date_string == None:
            log.info("Price Date not supplied. Using current date")
            current_price_date = datetime.now()
        else:
            current_price_date = recommendation_svc.validate_price_date(args.price_date)

        recommendation_svc.validate_commandline_parameters(
            year, month, current_price_date
        )
    else:
        current_price_date = datetime.now()
        (year, month) = recommendation_svc.compute_analysis_period(current_price_date)
        app_ns = args.app_namespace
    
    return (environment, ticker_file_name, output_size, month, year, current_price_date, app_ns)

#
# Main script
#

try:
    (environment, ticker_file_name, output_size, month, year, current_price_date, app_ns) = parse_params()

    log.info("Parameters:")
    log.info("Environment: %s" % environment)
    log.info("Ticker File: %s" % ticker_file_name)
    log.info("Output Size: %d" % output_size)
    log.info("Analysis Month: %d" % month)
    log.info("Analysis Year: %d" % year)    
    
    if (environment == "TEST"):
        log.info("reading ticker file from local filesystem")
        ticker_list = TickerFile.from_local_file(constants.ticker_data_dir, ticker_file_name).ticker_list
    else:
        log.info("reading ticker file from local s3 bucket")
        ticker_list = TickerFile.from_s3_bucket(ticker_file_name, app_ns).ticker_list
    

    strategy = PriceDispersionStrategy(ticker_list, year, month, output_size)
    
    log.info("Performing Recommendation Algorithm")
    recommendation_set = strategy.generate_recommendation()
    recommendation_dataframe = strategy.recommendation_dataframe
    raw_dataframe = strategy.raw_dataframe

    log.info("Pricing securities")
    raw_dataframe = calculator.mark_to_market(strategy.raw_dataframe, current_price_date)
    recommendation_dataframe = calculator.mark_to_market(strategy.recommendation_dataframe, current_price_date)

    log.info("")
    log.info("Recommended Securities")
    log.info(util.format_dict(recommendation_set.to_dict()))
    log.info("")

    log.info("Recommended Securities Return: %.2f%%" % (recommendation_dataframe['actual_return'].mean()*100))
    log.info("Average Return: %.2f%%" % (raw_dataframe['actual_return'].mean()*100))
    log.info("")
    log.info("Analysis Period - %d/%d, Actual Returns as of: %s" % (month, year, datetime.strftime(current_price_date, '%Y/%m/%d')))

    print(raw_dataframe[['analysis_period', 'ticker', 'dispersion_stdev_pct', 'analyst_expected_return', 'actual_return', 'decile']].to_string(index=False))

    if environment == "PRODUCTION":
        recommendation_set.save_to_s3(app_ns)
        recommendation_set.send_sns_notification(app_ns)

except Exception as e:
    log.error("Could run script, because: %s" % (str(e)))
    exit(-1)

