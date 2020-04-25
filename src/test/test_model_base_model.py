import unittest
import botocore
from unittest.mock import patch
from exception.exceptions import ValidationError, AWSError
from model.base_model import BaseModel
from cloud import aws_service_wrapper


class TestModel(BaseModel):
    
    schema = {}

    model_s3_folder_prefix = "test"
    model_s3_object_name = "test"

    model_name = "Portfolio"


class TestBaseModel(unittest.TestCase):

    def test_from_s3_with_boto_error_1(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value', \
            return_value="some_s3_bucket"), \
            patch.object(aws_service_wrapper, 's3_download_object', \
            side_effect=AWSError("test exception", None)):

            with self.assertRaises(AWSError):
                TestModel.from_s3("sa")

    def test_from_s3_with_boto_error_2(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value', \
            side_effect=AWSError("test exception", None)), \
            patch.object(aws_service_wrapper, 's3_download_object', \
            return_value=None):

            with self.assertRaises(AWSError):
                TestModel.from_s3("sa")

    def test_save_to_s3_with_boto_error(self):
        with patch.object(aws_service_wrapper, 'cf_read_export_value', \
            return_value="some_s3_bucket"), \
            patch.object(aws_service_wrapper, 's3_upload_ascii_string', \
            side_effect=AWSError("test exception", None)):

            with self.assertRaises(AWSError):
                t = TestModel()
                t.save_to_s3("sa")