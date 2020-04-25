"""valuate_security.py

"""
import argparse
import logging
from exception.exceptions import BaseError
from data_provider import intrinio_data
from data_provider import intrinio_util
from datetime import datetime
from support import util
from strategies.price_dispersion_strategy import PriceDispersionStrategy
from strategies import calculator
from cloud import aws_service_wrapper
from support import logging_definition

#
# Main script
#

description = """ This script is used for testing purposes only
              """


parser = argparse.ArgumentParser(description=description)
log = logging.getLogger()

args = parser.parse_args()

ticker_list = []

try:
    strategy = PriceDispersionStrategy(['AAPL', 'MSFT'], 2019, 10, 3)
    rec = strategy.generate_recommendation()

    df = calculator.mark_to_market(strategy.raw_dataframe, datetime.now())

    print(df)

    #print(aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute']))
    
except Exception as e:
    logging.error("Could run script, because, %s" % (str(e)))
    exit(-1)
