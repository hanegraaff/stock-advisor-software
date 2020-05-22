"""Author: Mark Hanegraaff -- 2020

This module provides a central place to test connectivity to Intrino, AWS and
TDAmeritrade. The methods provided here will execute read only operations,
and if a problem is found, it will rewrite the exception to indicate that
connection test failed while preserving the root cause.
"""


import logging
from datetime import datetime
from connectors import aws_service_wrapper, intrinio_data, td_ameritrade
from exception.exceptions import AWSError, TradeError, DataError
from support import constants

log = logging.getLogger()

def test_aws_connectivity():
    '''
        Tests the connection to AWS by reading a cloudformation export.
        Raises an AWSError if any errors are found
    '''
    log.info("Testing AWS connectivity")
    try:
        aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES)
        log.info("AWS connectivity test successful")
    except AWSError as awe:
        raise AWSError("AWS connectivity test failed", awe.cause)


def test_intrinio_connectivity():
    '''
        Makes a direct call to the intrio API (bypassing the cache) to verify the API
        key is still valid
    '''
    log.info("Testing Intrinio connectivity")
    try:
        intrinio_data.test_api_endpoint()
        log.info("Intrinio connectivity test successful")
    except DataError as de:
        raise DataError("Intrino Connectivity Test failed", de.cause)

def test_tdameritrade_connectivity():
    '''
        Makes a direct call to the intrio API (bypassing the cache) to verify the API
        key is still valid
    '''
    log.info("Testing TDAmeritrade connectivity")
    try:
        td_ameritrade.equity_market_open(datetime.now())
        log.info("TDAmeritrade connectivity test successful")
    except TradeError as de:
        raise TradeError("TDAmeritrade Connectivity Test failed", de.cause, None)

def test_all_connectivity():
    '''
        Convenience function to test all connectivity at once
    '''

    test_aws_connectivity()
    test_intrinio_connectivity()
    test_tdameritrade_connectivity()
