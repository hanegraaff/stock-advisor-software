"""Author: Mark Hanegraaff -- 2020
"""
from datetime import datetime, timedelta
from copy import deepcopy
import uuid
import pytz
import logging
from exception.exceptions import ValidationError
from model.base_model import BaseModel
from support import constants, util
import dateutil.parser as parser
from connectors import intrinio_data

log = logging.getLogger()


class Portfolio(BaseModel):
    """
        A data structure representing a portfolio.
        Portfolios are created and maintained by the Portfolio Manager service.
    """

    schema = {
        "type": "object",
        "required": [
            "portfolio_id", "portfolio_type", "creation_date", "last_updated", "open_positions"
        ],
        "properties": {
            "portfolio_id": {"type": "string"},
            "portfolio_type": {"type": "string"},
            "creation_date": {
                "type": "string",
                "format": "date-time"
            },
            "last_updated": {
                "type": "string",
                "format": "date-time"
            },
            "open_positions": {
                "type": "array",
                "minItems": 1,
                "items": { "$ref": "#/definitions/position"},
            }
        },
        "additionalProperties": False
    }

    model_s3_folder_prefix = constants.S3_PORTFOLIO_FOLDER_PREFIX

    model_name = "Portfolio"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)

    def get_position_securities(self):
        '''
            Returns all portfolio securities as a list
        '''
        return [open_position['ticker_symbol'] for open_position in self.model['open_positions']]

    def get_position(self, ticker_symbol: str):
        '''
            Returns a position dictionary given a ticker symbol.
            If the ticker symbol does not exist, retun None
        '''
        for position in self.model['open_positions']:
            if position['ticker_symbol'] == ticker_symbol:
                return position
        return None  

    def copy(self):
        '''
            returns a copy of the portfolio
        '''
        return deepcopy(self)
