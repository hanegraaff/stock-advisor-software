"""Author: Mark Hanegraaff -- 2020
"""
from datetime import datetime, date, timedelta
import uuid
import pytz
import dateutil.parser as parser
from exception.exceptions import ValidationError
from connectors import aws_service_wrapper
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
            "set_id", "creation_date", "valid_from", "valid_to",
            "price_date", "strategy_name", "security_type", "securities_set"
        ],
        "properties": {
            "set_id": {"type": "string"},
            "creation_date": {
                "type": "string",
                "format": "date-time"
            },
            "valid_from": {
                "type": "string",
                "format": "date"
            },
            "valid_to": {
                "type": "string",
                "format": "date"
            },
            "price_date": {
                "type": "string",
                "format": "date"
            },
            "strategy_name": {
                "type": "string",
                "minLength": 1
            },
            "security_type": {
                "type": "string",
                "minLength": 1
            },
            "securities_set": {
                "type": "array",
                "minItems": 0,
                "items": {
                    "type": "object",
                    "required": [
                        "ticker_symbol", "price"
                    ],
                    "properties": {
                        "ticker_symbol": {"type": "string"},
                        "price": {"type": "number"}
                    }
                }
            }
        }
    }

    model_s3_folder_prefix = constants.S3_RECOMMENDATION_SET_FOLDER_PREFIX
    model_name = "Security Recommendation Set"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)

    @classmethod
    def from_parameters(cls, creation_date: datetime, valid_from: date,
                        valid_to: date, price_date: date,
                        strategy_name: str, security_type: str, securities_set: dict):
        '''
            Initializes This class by supplying all required parameters.

            The "securities_set" is a ticker->price dictionary. E.g.

            {
                'AAPL': 123.45,
                'XO' : 234.56,
                ...
            }
        '''

        '''if (strategy_name is None or strategy_name == "" or security_type is None or
                security_type == "" or securities_set is None or len(securities_set) == 0):
            raise ValidationError(
                "Could not initialize Portfolio objects from parameters", None)
        '''

        try:
            cls.model = {
                "set_id": str(uuid.uuid1()),
                "creation_date": util.datetime_to_iso_utc_string(creation_date),
                "valid_from": valid_from.strftime("%Y-%m-%d"),
                "valid_to": valid_to.strftime("%Y-%m-%d"),
                "price_date": price_date.strftime("%Y-%m-%d"),
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
            raise ValidationError(
                "Could not initialize Portfolio objects from parameters", e)

        return cls.from_dict(cls.model)

    def is_current(self, comparison_date: date):
        """
            Returns True if this recommendation set is still current.
        """
        valid_from = parser.parse(
            self.model['valid_from']).date()

        valid_to = parser.parse(
            self.model['valid_to']).date()

        return valid_from <= comparison_date <= valid_to
