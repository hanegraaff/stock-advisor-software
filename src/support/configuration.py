"""Author: Mark Hanegraaff -- 2020
"""

import os
import logging
import configparser
from exception.exceptions import ValidationError, AWSError
from connectors import aws_service_wrapper
from support import constants

log = logging.getLogger()


class Configuration():
    '''
        An INI style configuration file used to store the various
        parameters used by the strategy classes. Strategies must
        be able to initialize using this configuration alone
    '''

    config = None

    @classmethod
    def from_local_config(cls, config_filename: str):
        '''
            Downloads a configuration file
        '''
        cls.config = configparser.ConfigParser(allow_no_value=True)

        try:
            cls.config_file = open(
                "%s%s" % (constants.CONFIG_FILE_PATH, config_filename))
            cls.config.read_file(cls.config_file)
        except Exception as e:
            raise ValidationError("Could not load Configuration", e)

        # make sure the file is not empty. If it is, raise an exception
        if len(cls.config.sections()) == 0:
            cls.config_file.close()
            raise ValidationError(
                "Configuration file [%s] does not include any sections" % constants.CONFIG_FILE_PATH, None)

        cls.config_file.close()
        return cls()

    @classmethod
    def try_from_s3(cls, config_filename: str, app_ns: str):
        '''
            Downloads a configuration file from S3 given the supplied file (object) name
            and application namespace used to read cloudformation exports.

            If the file does not exist use the local one and upload it to S3
        '''
        try:
            s3_data_bucket_name = aws_service_wrapper.cf_read_export_value(
                constants.s3_data_bucket_export_name(app_ns))

            s3_object_name = "%s/%s" % (constants.S3_CONFIG_OLDER_PREFIX,
                                        config_filename)

            dest_filename = "%s.s3download" % config_filename
            dest_path = "%s%s" % (constants.CONFIG_FILE_PATH,
                                  dest_filename)

            log.info("Downloading Configuration File: s3://%s/%s --> %s" %
                     (s3_data_bucket_name, s3_object_name, dest_path))
            aws_service_wrapper.s3_download_object(
                s3_data_bucket_name, s3_object_name, dest_path)

            return cls.from_local_config(dest_filename)
        except AWSError as awe:
            if awe.resource_not_found():
                log.debug(
                    "Configuration not found in S3. Looking for local alternatives")

                # Attempt to upload a local copy of the configuration if it
                # exists
                local_configuration_path = "%s%s" % (
                    constants.CONFIG_FILE_PATH, config_filename)

                if os.path.isfile(local_configuration_path):
                    log.debug("Attempting to upload %s --> s3://%s/%s" %
                              (local_configuration_path, s3_data_bucket_name, s3_object_name))
                    aws_service_wrapper.s3_upload_object(
                        local_configuration_path, s3_data_bucket_name, s3_object_name)

                    return cls.from_local_config(config_filename)
                else:
                    log.debug("No local alternatives found")
                    raise awe
            else:
                raise awe

    @property
    def config(self):
        '''
        '''
        return self.config

    def close(self):
        '''
            Close the underlining configuration file
        '''
        self.config_file.close()
