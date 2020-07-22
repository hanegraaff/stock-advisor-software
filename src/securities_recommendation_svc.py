"""securities_recommendation_svc.py

Securities Recommendation Service Main script.

Complete documentation can be found here:
https://github.com/hanegraaff/stock-advisor-software

"""
import argparse
import logging
import traceback
import pandas as pd
from datetime import datetime, timedelta
from connectors import aws_service_wrapper, connector_test
from exception.exceptions import ValidationError, AWSError
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies.macd_crossover_strategy import MACDCrossoverStrategy
from services import recommendation_svc
from model.recommendation_set import SecurityRecommendationSet
from support import constants, logging_definition, util
from support.configuration import Configuration


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

    description = """ 
                  Executes all available strategies and creates stock recommendations for each.
                  Recommendations are represented as JSON documents and are stored using S3.
                  
                  The command line input is an application namespace used to identify the AWS resources 
                  required by the service, namely the S3 bucket used to store the application inputs 
                  consisting of ticker lists and configuration, and the outputs consisting of
                  recommendation objects.
              """
    log.info("Parsing command line parameters")

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-app_namespace", help="Application namespace used to identify AWS resources", type=str, required=True)

    args = parser.parse_args()
    app_ns = args.app_namespace

    return app_ns


def main():
    """
        Main function for this script
    """
    try:
        #app_ns = parse_params()
        app_ns = 'sa'

        log.info("Parameters:")
        log.info("Application Namespace: %s" % app_ns)

        business_date = util.get_business_date(
            constants.BUSINESS_DATE_DAYS_LOOKBACK, constants.BUSINESS_DATE_CUTOVER_TIME)
        log.info("Business Date is: %s" % business_date)

        # test all connectivity upfront, so if there any issues
        # the problem becomes more apparent
        connector_test.test_aws_connectivity()
        connector_test.test_intrinio_connectivity()

        log.info('Loading Strategy Configuration "%s" from S3' %
                 constants.STRATEGY_CONFIG_FILE_NAME)
        configuration = Configuration.try_from_s3(
            constants.STRATEGY_CONFIG_FILE_NAME, app_ns)

        log.info("Initalizing Trading Strategies")
        strategies = [
            PriceDispersionStrategy.from_configuration(configuration, app_ns),
            MACDCrossoverStrategy.from_configuration(configuration, app_ns)
        ]

        notification_list = []
        for strategy in strategies:
            recommendation_set = None
            try:
                log.info("Executing %s strategy" % strategy.STRATEGY_NAME)
                recommendation_set = SecurityRecommendationSet.from_s3(
                    app_ns, strategy.S3_RECOMMENDATION_SET_OBJECT_NAME)
            except AWSError as awe:
                if not awe.resource_not_found():
                    raise awe
                log.info("No recommendation set was found in S3.")

            if recommendation_set == None  \
                    or not recommendation_set.is_current(business_date):

                strategy.generate_recommendation()
                strategy.display_results()

                recommendation_set = strategy.recommendation_set

                recommendation_set.save_to_s3(
                    app_ns, strategy.S3_RECOMMENDATION_SET_OBJECT_NAME)

                notification_list.append(recommendation_set)
            else:
                log.info(
                    "Recommendation set is still valid. There is nothing to do")

        recommendation_svc.notify_new_recommendation(
            notification_list, app_ns)
    except Exception as e:
        stack_trace = traceback.format_exc()
        log.error("Could run script, because: %s" % (str(e)))
        log.error(stack_trace)

        aws_service_wrapper.notify_error(e, "Securities Recommendation Service",
                                            stack_trace, app_ns)

if __name__ == "__main__":
    main()
