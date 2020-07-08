"""Author: Mark Hanegraaff -- 2020
"""
import logging
import os
from exception.exceptions import AWSError
from model.base_model import BaseModel
from support import constants, util
from connectors import aws_service_wrapper

log = logging.getLogger()


class TickerList(BaseModel):
    """
        A data model representing a list of ticker symbols supplied as
        an input to a strategy. This model contails a list of ticker symbols
        and some descriptors (name, type) associated with them.
    """

    schema = {
        "type": "object",
        "required": [
            "list_name", "list_type", "ticker_symbols"
        ],
        "properties": {
            "list_name": {"type": "string"},
            "list_type": {"type": "string"},
            "comparison_symbol": {"type": "string"},
            "ticker_symbols": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "string"
                }
            }
        }
    }

    model_s3_folder_prefix = constants.S3_TICKER_FILE_FOLDER_PREFIX
    model_name = "TickerList"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)

    @classmethod
    def try_from_s3(cls, app_ns: str, ticker_file_name: str):
        '''
            Override for BaseModel.from_s3

            loads the model from S3. If one is not found look for a local alternative
            and upload it to the same bucket. This is done to eliminate the need to
            pre-populate S3 with any data when the application is first installed.
        '''

        try:
            return cls.from_s3(app_ns, ticker_file_name)
        except AWSError as awe:
            if awe.resource_not_found():
                log.debug("File not found in S3. Looking for local alternatives")

                s3_object_path = "%s/%s" % (cls.model_s3_folder_prefix,
                                            ticker_file_name)

                log.debug(
                    "Reading S3 Data Bucket location from CloudFormation Exports")
                s3_data_bucket_name = aws_service_wrapper.cf_read_export_value(
                    constants.s3_data_bucket_export_name(app_ns))

                # Attempt to upload a local copy of the file if it exists
                local_ticker_path = '%s/%s' % (
                    constants.TICKER_DATA_DIR, ticker_file_name)

                if os.path.isfile(local_ticker_path):
                    log.debug("Attempting to upload %s --> s3://%s/%s" %
                              (local_ticker_path, s3_data_bucket_name, s3_object_path))

                    aws_service_wrapper.s3_upload_object(
                        local_ticker_path, s3_data_bucket_name, s3_object_path)

                    return cls.from_local_file(local_ticker_path)
                else:
                    log.debug("No local alternatives found")
                    raise awe
            else:
                raise awe

    @property
    def ticker_symbols(self):
        '''
            ticker list getter. Returns the ticker symbols list
        '''
        return self.model['ticker_symbols']
