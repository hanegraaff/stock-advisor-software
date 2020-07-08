"""Author: Mark Hanegraaff -- 2020
"""
from abc import ABC, abstractmethod
import jsonschema
import json
from copy import deepcopy
import logging
from datetime import datetime
from jsonschema import validate
from exception.exceptions import ValidationError
from connectors import aws_service_wrapper
from support import constants, util

log = logging.getLogger()


class BaseModel(ABC):
    '''
        Base class for all domain model objects used by this application.
    '''

    schema = {}
    model_s3_folder_prefix = ""

    model_name = ""
    model = {}

    @abstractmethod
    def __init__(self, model_dict: dict):
        self.model = deepcopy(model_dict)

    @classmethod
    def from_dict(cls, model_dict):
        '''
            Loads the model from a dictionary object
        '''
        try:
            validate(model_dict, cls.schema,
                     format_checker=jsonschema.FormatChecker())
        except Exception as e:
            raise ValidationError("Could not initialize from dictionary", e)

        return cls(model_dict)

    @classmethod
    def from_local_file(cls, model_path: str):
        '''
            Loads the model from a local file
        '''
        try:
            with open(model_path) as file:
                model_str = file.read()
            model_dict = json.loads(model_str)
        except Exception as e:
            raise ValidationError("Could not load %s" % cls.model_name, e)

        return cls.from_dict(model_dict)

    @classmethod
    def from_s3(cls, app_ns: str, s3_object_name: str):
        '''
            loads the model from S3 using preconfigured object names
        '''

        util.create_dir(constants.APP_DATA_DIR)

        s3_data_bucket_name = aws_service_wrapper.cf_read_export_value(
            constants.s3_data_bucket_export_name(app_ns))
        s3_object_path = "%s/%s" % (cls.model_s3_folder_prefix,
                                    s3_object_name)
        dest_path = "%s/%s" % (constants.APP_DATA_DIR,
                               s3_object_name)

        log.info("Downloading %s: s3://%s/%s --> %s" %
                 (cls.model_name, s3_data_bucket_name, s3_object_path, dest_path))
        aws_service_wrapper.s3_download_object(
            s3_data_bucket_name, s3_object_path, dest_path)

        return cls.from_local_file(dest_path)

    def validate_model(self):
        '''
            (Re)validates the model
        '''
        try:
            validate(self.model, self.schema,
                     format_checker=jsonschema.FormatChecker())
        except Exception as e:
            raise ValidationError(
                "Could not validate %s model" % self.model_name, e)

    def to_dict(self):
        '''
            returns the model as a dictionary
        '''
        return self.model

    def save_to_s3(self, app_ns: str, s3_object_name: str):
        '''
            Uploads the model to S3

            Parameters
            ----------
            app_ns : str
                The application namespace supplied to the command line
                used to identify the appropriate CloudFormation exports
        '''

        self.validate_model()

        s3_data_bucket_name = aws_service_wrapper.cf_read_export_value(
            constants.s3_data_bucket_export_name(app_ns))
        s3_object_path = "%s/%s" % (self.model_s3_folder_prefix,
                                    s3_object_name)

        log.info("Uploading %s to S3: s3://%s/%s" %
                 (self.model_name, s3_data_bucket_name, s3_object_path))
        aws_service_wrapper.s3_upload_ascii_string(
            util.format_dict(self.model), s3_data_bucket_name, s3_object_path)
