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
from cloud import aws_service_wrapper

#
# Main script
#

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')

description = """ This script is used for testing purposes only
              """


parser = argparse.ArgumentParser(description=description)
log = logging.getLogger()

args = parser.parse_args()

ticker_list = []

try:
    '''strategy = PriceDispersionStrategy(['AAPL', 'MSFT'], 2019, 10, 3)
    portfolio = strategy.generate_portfolio()
    print(util.format_dict(portfolio.to_dict()))'''

    print(aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute']))
    
except Exception as e:
    logging.error("Could run script, because, %s" % (str(e)))
    exit(-1)
