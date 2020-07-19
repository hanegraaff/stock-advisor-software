"""Author: Mark Hanegraaff -- 2020
"""
from datetime import datetime, timedelta
from copy import deepcopy
import uuid
import pytz
from jsonschema import RefResolver
import model.shared_model_shema as sms
import logging
from exception.exceptions import ValidationError
from model.base_model import BaseModel
from support import constants, util
import dateutil.parser as parser
from connectors import intrinio_data

log = logging.getLogger()


class Positions(BaseModel):
    """
        A data structure representing a set of positions, open and closed positions
        are stored in different documents.

        Positions are created and maintained by the Portfolio Manager service.
    """

    schema = {
        "type": "object",
        "required": [
            "positions_id", "positions_type", "creation_date", "last_updated", "positions"
        ],
        "properties": {
            "test_field": { "$ref": "#/definitions/test" },
            "positions_id": {"type": "string"},
            "positions_type": {"type": "string"},
            "creation_date": {
                "type": "string",
                "format": "date-time"
            },
            "last_updated": {
                "type": "string",
                "format": "date-time"
            },
            "positions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": [
                        "ticker_symbol", "ls_indicator", "strategy_name",
                        "quantity", "pnl", "open"
                    ],
                    "properties": {
                        "ticker_symbol": {"type": "string"},
                        "ls_indicator":{
                            "type": "string",
                            "enum": ["LONG", "SHORT"]
                        },
                        "strategy_name": {"type": "string"},
                        "quantity": {"type": "number"},
                        "pnl": {"type": "number"},
                        "open":{
                            "type": "object",
                            "required": [
                                "price", "date", "order_id", "reason"
                            ],
                            "properties": {
                                "price": {"type": "number"},
                                "date": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "order_id": {"type": "string"},
                                "reason": {"type": "string"},
                            }
                        },
                        "close":{
                            "type": "object",
                            "required": [
                                "price", "date", "order_id", "reason"
                            ],
                            "properties": {
                                "price": {"type": "number"},
                                "date": {
                                    "type": "string",
                                    "format": "date-time"
                                },
                                "order_id": {"type": "string"},
                                "reason": {"type": "string"},
                            }
                        }
                    }
                }
            }
        }
    }

    ref_resolver = RefResolver.from_schema(sms.SHARED_MODEL_SCHEMA)

    model_s3_folder_prefix = constants.S3_POSITIONS_FOLDER_PREFIX

    model_name = "Positions"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)


    def reprice(self, price_date: datetime):
        '''
            Reads the current prices, computes the latest returns
            and updates the portfolio object.
        '''
        pass


    def copy(self):
        '''
            returns a copy of the portfolio
        '''
        return deepcopy(self)
