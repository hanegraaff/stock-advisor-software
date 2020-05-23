"""Author: Mark Hanegraaff -- 2020
    Testing class for the model.recommendation_set module
"""
import unittest
from unittest.mock import patch
from exception.exceptions import ValidationError, FileSystemError, AWSError
from model.ticker_file import TickerFile
from connectors import aws_service_wrapper
from support import constants
import os


class TestModelTickerFile(unittest.TestCase):

    """
        Testing class for the model.recommendation_set module
    """

    def test_from_s3_bucket_valid(self):
        expected_return = ['TICKER-A', 'TICKER-B']

        with patch.object(TickerFile, 'from_local_file',
                          return_value=TickerFile(expected_return)), \
            patch.object(aws_service_wrapper, 's3_download_object',
                         return_value=None), \
            patch.object(aws_service_wrapper, 'cf_list_exports',
                         return_value={
                             constants.s3_data_bucket_export_name('sa'): "test-bucket"
                         }):

            ticker_file = TickerFile.from_s3_bucket('ticker-file', 'sa')
            actual_return = ticker_file.ticker_list

            self.assertListEqual(expected_return, actual_return)

    def test_from_s3_bucket_aws_error(self):
        with patch.object(aws_service_wrapper, 's3_download_object',
                          return_value=None), \
            patch.object(aws_service_wrapper, 'cf_list_exports',
                         side_effect=AWSError("test", None)):

            with self.assertRaises(AWSError):
                TickerFile.from_s3_bucket('ticker-file', 'sa')

        with patch.object(aws_service_wrapper, 's3_download_object',
                          side_effect=AWSError("test", None)), \
            patch.object(aws_service_wrapper, 'cf_list_exports',
                         return_value={
                             constants.s3_data_bucket_export_name('sa'): "test-bucket"
                         }):

            with self.assertRaises(AWSError):
                TickerFile.from_s3_bucket('ticker-file', 'sa')

    def test_get_ticker_no_exports(self):
        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          return_value={}):

            with self.assertRaises(ValidationError):
                TickerFile.from_s3_bucket('ticker-file', 'sa')

    def test_from_s3_bucket_exception_upload_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            a local alternative is found, it will self heal by
            restoring the s3 file
        '''
        expected_return = ['TICKER-A', 'TICKER-B']

        with patch.object(TickerFile, 'from_local_file',
                          return_value=TickerFile(expected_return)), \
            patch.object(aws_service_wrapper, 'cf_list_exports',
                         return_value={
                             constants.s3_data_bucket_export_name('sa'): "test-bucket"
                         }),\
            patch.object(aws_service_wrapper, 's3_download_object',
                         side_effect=AWSError(
                             "test", Exception(
                                 "An error occurred (404) when calling the HeadObject operation: Not Found")
                         )
                         ),\
            patch.object(aws_service_wrapper, 's3_upload_object',
                         return_value=None),\
            patch.object(os.path, 'isfile',
                         return_value=True):

            ticker_file = TickerFile.from_s3_bucket('ticker-file', 'sa')
            actual_return = ticker_file.ticker_list

            self.assertListEqual(expected_return, actual_return)

    def test_from_s3_bucket_exception_no_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            no local alternative is found, it throws an exception.
        '''

        with patch.object(aws_service_wrapper, 'cf_list_exports',
                          return_value={
                              constants.s3_data_bucket_export_name('sa'): "test-bucket"
                          }),\
            patch.object(aws_service_wrapper, 's3_download_object',
                         side_effect=AWSError(
                             "test", Exception("Download Exception")
                         )
                         ),\
            patch.object(os.path, 'isfile',
                         return_value=False):

            try:
                TickerFile.from_s3_bucket('ticker-file', 'sa')
            except AWSError as awe:
                self.assertTrue("Download Exception" in str(awe))
