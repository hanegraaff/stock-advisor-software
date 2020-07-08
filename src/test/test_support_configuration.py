"""Author: Mark Hanegraaff -- 2020
    Testing class for the support.configuration
"""
import unittest
import os
from unittest.mock import patch
from support.configuration import Configuration
from support import constants
from exception.exceptions import ValidationError, AWSError
from connectors import aws_service_wrapper


class TestConfiguration(unittest.TestCase):

    """
        Testing class for the support.configuration
    """

    '''
        from_local_config tests
    '''

    def test_init_no_config(self):
        with self.assertRaises(ValidationError):
            Configuration.from_local_config("does_not_exist.ini")

    def test_init_empty_config(self):
        with patch('support.constants.CONFIG_FILE_PATH', "./test/config-unittest-bad/"):
            with self.assertRaises(ValidationError):
                Configuration.from_local_config("empty-test-config.ini")

    '''
        from_s3 tests
    '''

    def test_from_s3_bucket_exception_upload_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            a local alternative is found, it will self heal by
            restoring the s3 file
        '''

        configuration = Configuration.from_local_config(
            constants.STRATEGY_CONFIG_FILE_NAME)

        with patch.object(Configuration, 'from_local_config',
                          return_value=configuration), \
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
                         return_value=None) as mock_s3_upload_object,\
            patch.object(os.path, 'isfile',
                         return_value=True):

            Configuration.try_from_s3(
                constants.STRATEGY_CONFIG_FILE_NAME, 'sa')

            # assert that s3_upload_object method was called once
            self.assertEqual(mock_s3_upload_object.call_count, 1)

    def test_from_s3_bucket_exception_no_local_file(self):
        '''
            Tests that if the file was not found in s3, and
            a local no alternative is found, an exception will be
            thrown
        '''

        configuration = Configuration.from_local_config(
            constants.STRATEGY_CONFIG_FILE_NAME)

        with patch.object(Configuration, 'from_local_config',
                          return_value=configuration), \
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
            patch.object(os.path, 'isfile',
                         return_value=False):

            with self.assertRaises(AWSError):
                Configuration.try_from_s3(
                    constants.STRATEGY_CONFIG_FILE_NAME, 'sa')
