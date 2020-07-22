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
        A data structure representing a set of positions.
        Positions are created and maintained by the Portfolio Manager service.
    """

    schema = {
        "type": "object",
        "required": [
            "positions_id", "positions_type", "creation_date", "last_updated", "positions"
        ],
        "properties": {
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
                "items": { "$ref": "#/definitions/position"},
            }
        },
        "additionalProperties": False
    }

    model_s3_folder_prefix = constants.S3_POSITIONS_FOLDER_PREFIX

    model_name = "Positions"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)


    def add_position(self, position: dict):
        '''
            appends a new position to the list.
            The position is a dictionary that must match this format
            {"$ref": "#/definitions/position"}
        '''
        pass


    def copy(self):
        '''
            returns a copy of the portfolio
        '''
        return deepcopy(self)
