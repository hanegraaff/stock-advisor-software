import unittest
import botocore
from unittest.mock import patch
from exception.exceptions import AWSError
from cloud import aws_service_wrapper
from test import nop


class TestCloudAWSServiceWrapper(unittest.TestCase):

    '''
        list_exports tests
    '''

    def test_cf_list_exports_with_boto_exception(self):
        with patch.object(aws_service_wrapper.cf_client, 'get_paginator', \
                    side_effect=botocore.exceptions.BotoCoreError()):

            with self.assertRaises(AWSError):
                aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute'])

    def test_cf_list_exports_no_data(self):
        with patch.object(aws_service_wrapper.cf_client, 'list_exports', \
                    return_value={
                        "Exports": []
                    }):

            self.assertEqual(
                aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute']),
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
                aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute']),
                {
                    "export-name-1": "export-value-1"
                }
            )

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
                    aws_service_wrapper.cf_list_exports(['app-infra-base', 'app-infra-compute'])

                    
