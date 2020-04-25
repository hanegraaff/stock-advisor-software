from datetime import datetime, timedelta
import uuid 
import pytz
import json
import dateutil.parser as parser
from exception.exceptions import ValidationError
from cloud import aws_service_wrapper
from support import constants, util
from model.base_model import BaseModel
import logging

log = logging.getLogger()

class SecurityRecommendationSet(BaseModel):
    """
        A data structure representing a set of recommendations generated
        by a selection strategy
    """

    schema = {
        "type": "object",
        "required": [
            "set_id", "creation_date", "analysis_start_date", "analysis_end_date",
            "price_date", "strategy_name", "security_type", "securities_set"
        ],
        "properties" : {
            "set_id" : {"type" : "string"},
            "creation_date" : {
                "type" : "string",
                "format" : "date-time"
            },
            "analysis_start_date" : {
                "type" : "string",
                "format" : "date-time"
            },
            "analysis_end_date" : {
                "type" : "string",
                "format" : "date-time"
            },
            "price_date" : {
                "type" : "string",
                "format" : "date-time"
            },
            "strategy_name" : {
                "type" : "string",
                "minLength": 1
            },
            "security_type" : {
                "type" : "string",
                "minLength" : 1
            },
            "securities_set" : {
                "type" : "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                       "ticker_symbol", "price"
                    ],
                    "properties" : {
                        "ticker_symbol": {"type": "string"},
                        "price" : {"type" : "number"}
                    }
                }
            }
        }   
    }

    model_s3_folder_prefix = constants.S3_RECOMMENDATION_SET_FOLDER_PREFIX
    model_s3_object_name = constants.S3_RECOMMENDATION_SET_OBJECT_NAME

    model_name = "Security Recommendation Set"


    def __init__(self):
        pass


    @classmethod
    def from_parameters(cls, creation_date : datetime, analysis_start_date : datetime,
            analysis_end_date : datetime, price_date : datetime,
            strategy_name : str, security_type : str, securities_set : dict):
        '''
            Initializes This class by supplying all required parameters.

            The "securities_set" is a ticker->price dictionary. E.g.

            {
                'AAPL': 123.45,
                'XO' : 234.56,
                ...
            }
        '''

        if (strategy_name == None or strategy_name == ""  or security_type == None or
            security_type == "" or securities_set == None or len(securities_set) == 0):
            raise ValidationError("Could not initialize Portfolio objects from parameters", None)

        try:
            cls.model = {
                "set_id": str(uuid.uuid1()),
                "creation_date": util.date_to_iso_utc_string(creation_date),
                "analysis_start_date" : util.date_to_iso_string(analysis_start_date),
                "analysis_end_date" : util.date_to_iso_string(analysis_end_date),
                "price_date": util.date_to_iso_string(price_date),
                "strategy_name": strategy_name,
                "security_type": security_type,
                "securities_set": []
            }

            for ticker in securities_set.keys():
                cls.model['securities_set'].append({
                    "ticker_symbol": ticker,
                    "price": securities_set[ticker]
                })
        except Exception as e:
            raise ValidationError("Could not initialize Portfolio objects from parameters", e)

        
        return cls.from_dict(cls.model)

    
    def is_current(self):
        """
            Returns True if this recommendation set is still current.

            A set is current as long as the analysis end date falls in the
            previous month relative to the calendar date
        """
        valid_until = parser.parse(self.model['analysis_end_date']) + timedelta(days=1)
        current_month = datetime.now().month

        return valid_until.month == current_month
           

    def send_sns_notification(self, app_ns : str):
        '''
            Sends an SNS notification indicating that a new recommendation has been generated

            Parameters
            ----------
            app_ns : str
                The application namespace supplied to the command line
                used to identify the appropriate CloudFormation exports
        '''

        recommnedation_month = parser.parse(self.model['analysis_end_date']) + timedelta(days=1)

        formatted_ticker_message = ""
        for security in self.model['securities_set']:
            formatted_ticker_message += "Ticker Symbol: %s\n" % security['ticker_symbol']
    
        sns_topic_arn = aws_service_wrapper.cf_read_export_value(constants.sns_app_notifications_topic_arn(app_ns))
        subject = "New Stock Recommendation Available"
        message = "A New Stock Recommendation is available for the month of %s\n" % recommnedation_month.strftime("%B")
        message += "\n\n"
        message += formatted_ticker_message

        log.info("Publishing Recommendation set to SNS topic: %s" % sns_topic_arn)
        aws_service_wrapper.sns_publish_notification(sns_topic_arn, subject, message)

