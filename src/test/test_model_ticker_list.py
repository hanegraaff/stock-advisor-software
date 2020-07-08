"""Author: Mark Hanegraaff -- 2020
    Testing class for the model.ticker_list module
"""
import unittest
from unittest.mock import patch
from exception.exceptions import AWSError
from model.ticker_list import TickerList
from connectors import aws_service_wrapper
from support import constants
import os


class TestModelTickerList(unittest.TestCase):

    """
        Testing class for the model.ticker_list module
    """

    def test_from_s3_bucket_exception_upload_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            a local alternative is found, it will self heal by
            restoring the s3 file
        '''

        ticker_list = TickerList.from_dict(
            {
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": [
                    "AAPL",
                    "AXP",
                    "BA"
                ]
            }
        )

        with patch.object(TickerList, 'from_local_file',
                          return_value=ticker_list), \
            patch.object(aws_service_wrapper, 'cf_list_exports',
                         return_value={
                             constants.s3_data_bucket_export_name('sa'): "test-bucket"
                         }),\
            patch.object(TickerList, 'from_s3',
                         side_effect=AWSError(
                             "test", Exception(
                                 "An error occurred (404) when calling the HeadObject operation: Not Found")
                         )
                         ),\
            patch.object(aws_service_wrapper, 's3_upload_object',
                         return_value=None) as mock_s3_upload_object,\
            patch.object(os.path, 'isfile',
                         return_value=True):

            ticker_file = TickerList.try_from_s3('sa', 'ticker-file')

            # assert that s3_upload_object method was called once
            self.assertEqual(mock_s3_upload_object.call_count, 1)

    def test_from_s3_bucket_exception_no_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            a local alternative is found, it will self heal by
            restoring the s3 file
        '''

        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          return_value={
                              constants.s3_data_bucket_export_name('sa'): "test-bucket"
                          }),\
            patch.object(TickerList, 'from_s3',
                         side_effect=AWSError(
                             "test", Exception(
                                 "An error occurred (404) when calling the HeadObject operation: Not Found")
                         )
                         ),\
            patch.object(aws_service_wrapper, 's3_upload_object',
                         return_value=None) as mock_s3_upload_object,\
            patch.object(os.path, 'isfile',
                         return_value=False):

            with self.assertRaises(AWSError):
                TickerList.try_from_s3('sa', 'ticker-file')

    def test_ticker_list_matches(self):
        ticker_list = TickerList.from_dict(
            {
                "list_name": "DOW30",
                "list_type": "US_EQUITIES",
                "comparison_symbol": "DIA",
                "ticker_symbols": [
                    "AAPL",
                    "AXP",
                    "BA"
                ]
            }
        )

        self.assertListEqual(ticker_list.ticker_symbols,
                             ticker_list.model['ticker_symbols'])

    def test_from_s3_bucket_exception(self):
        '''
            Tests that if there was an error downloading the ticker file 
            from S3, it will thrown an exception
        '''

        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          return_value={
                              constants.s3_data_bucket_export_name('sa'): "test-bucket"
                          }),\
            patch.object(aws_service_wrapper, 's3_download_object',
                         side_effect=AWSError(
                             "test", Exception("Download Exception")
                         )
                         ):

            try:
                TickerList.try_from_s3('sa', 'ticker-file')
            except AWSError as awe:
                self.assertTrue("Download Exception" in str(awe))
