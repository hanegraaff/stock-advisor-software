import unittest
import botocore
from unittest.mock import patch
from exception.exceptions import AWSError
from cloud import aws_service_wrapper
from test import nop
from support import constants


class TestCloudAWSServiceWrapper(unittest.TestCase):

    def setUp(self):
        '''
            make sure to clear out the local cache before each test
            or results won't be predictible
        '''
        aws_service_wrapper.aws_response_cache = {}

    '''
        list_exports tests
    '''

    def test_cf_list_exports_with_boto_exception(self):
        with patch.object(aws_service_wrapper.cf_client, 'get_paginator', \
                    side_effect=botocore.exceptions.BotoCoreError()):

            with self.assertRaises(AWSError):
                aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES)

    def test_cf_list_exports_no_data(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                    return_value={
                        "Exports": []
                    }):

            self.assertEqual(
                aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES),
                {}
            )

    def test_cf_list_exports_none_input(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                return_value={
                    "Exports": []
                }):

            self.assertEqual(
                aws_service_wrapper.cf_list_exports(None),
                {}
            )

    def test_cf_list_exports_single_value(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                    return_value={
                        "Exports": [
                            {
                                "ExportingStackId": "arn:aws:cloudformation:us-east-1:acct:stack/app-infra-base/c9481160-6df5-11ea-ac9f-121b58656156",
                                "Name": "export-name-1",
                                "Value": "export-value-1"
                            }]
                        }):

            self.assertEqual(
                aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES),
                {
                    "export-name-1": "export-value-1"
                }
            )

    def test_cf_list_exports_verify_cache(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                return_value={
                    "Exports": [
                        {
                            "ExportingStackId": "arn:aws:cloudformation:us-east-1:acct:stack/app-infra-base/c9481160-6df5-11ea-ac9f-121b58656156",
                            "Name": "export-name-1",
                            "Value": "export-value-1"
                        }]
                    }):
                
                aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES)

        self.assertEqual(len(aws_service_wrapper.aws_response_cache), 1)

    def test_cf_list_exports_invalid_arn(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                return_value={
                    "Exports": [
                        {
                            "ExportingStackId": "INVALID_ARN",
                            "Name": "export-name-1",
                            "Value": "export-value-1"
                        }]
                    }):

            with self.assertRaises(AWSError):
                    aws_service_wrapper.cf_list_exports(constants.APP_CF_STACK_NAMES)

                    
    '''
        Upload/Download object test
    '''
    def test_s3_download_object_with_boto_exception(self):
        with patch.object(aws_service_wrapper.s3_client, 'download_file', \
                    side_effect=botocore.exceptions.BotoCoreError()):

            with self.assertRaises(AWSError):
                aws_service_wrapper.s3_download_object("bucket_name", "object_name", "./dest_path")


    def test_s3_upload_ascii_string_with_boto_exception(self):
        with patch.object(aws_service_wrapper.s3_client, 'put_object', \
                    side_effect=botocore.exceptions.BotoCoreError()):

            with self.assertRaises(AWSError):
                aws_service_wrapper.s3_upload_ascii_string("some string to upload", "s3_bucket_name", "s3_object_name")


    def test_sns_publish_notification_with_boto_exception(self):
        with patch.object(aws_service_wrapper.sns_client, 'publish', \
                    side_effect=botocore.exceptions.BotoCoreError()):

            with self.assertRaises(AWSError):
                aws_service_wrapper.sns_publish_notification("topic_arn", "subject", "message")