"""Author: Mark Hanegraaff -- 2020
    Testing class for the connectors.connector_test module
"""

import unittest
from unittest.mock import patch
from connectors import connector_test
from connectors import aws_service_wrapper, td_ameritrade, intrinio_data
from exception.exceptions import AWSError, TradeError, DataError


class TestConnectorsTest(unittest.TestCase):
    """
        Testing class for the connectors.connector_test module
    """

    def test_test_aws_connectivity_with_exception(self):
        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          side_effect=AWSError("Some Error", None)):

            with self.assertRaises(AWSError):
                connector_test.test_aws_connectivity()

    def test_test_aws_connectivity_success(self):
        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          return_value=None):

            connector_test.test_aws_connectivity()

    def test_test_intrinio_connectivity_with_exception(self):
        with patch.object(intrinio_data, 'test_api_endpoint',
                          side_effect=DataError("Some Error", None)):

            with self.assertRaises(DataError):
                connector_test.test_intrinio_connectivity()

    def test_test_intrinio_connectivity_success(self):
        with patch.object(intrinio_data, 'test_api_endpoint',
                          side_effect=None):

            connector_test.test_intrinio_connectivity()

    def test_test_tdameritrade_connectivity_with_exception(self):
        with patch.object(td_ameritrade, 'equity_market_open',
                          side_effect=TradeError("Some Error", None, None)):

            with self.assertRaises(TradeError):
                connector_test.test_tdameritrade_connectivity()

    def test_test_tdameritrade_connectivity_success(self):
        with patch.object(td_ameritrade, 'equity_market_open',
                          side_effect=None):

            connector_test.test_tdameritrade_connectivity()
