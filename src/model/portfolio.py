"""Author: Mark Hanegraaff -- 2020
"""
from datetime import datetime, timedelta
from copy import deepcopy
import uuid
import pytz
import json
import logging
from exception.exceptions import ValidationError
from model.base_model import BaseModel
from support import constants, util
import dateutil.parser as parser
from connectors import intrinio_data

log = logging.getLogger()


class Portfolio(BaseModel):
    """
        A data structure representing a portfolio based on a recommndation set.
        Portfolios are created and maintained by the Portfolio Manager service.

        It can be serialized into a json document that looks like this:
    """

    schema = {
        "type": "object",
        "required": [
            "portfolio_id", "set_id", "creation_date", "securities_set", "price_date"
        ],
        "properties": {
            "portfolio_id": {"type": "string"},
            "set_id": {"type": "string"},
            "creation_date": {
                "type": "string",
                "format": "date-time"
            },
            "price_date": {
                "type": "string",
                "format": "date"
            },
            "current_portfolio": {
                "type": "object",
                "properties": {
                    "securities": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": [
                                "ticker_symbol", "quantity", "purchase_date",
                                "purchase_price", "current_price", "current_returns",
                                "trade_state", "order_id"
                            ],
                            "properties": {
                                "ticker_symbol": {"type": "string"},
                                "quantity": {"type": "number"},
                                "purchase_date": {
                                    "type": [
                                        "string",
                                        "null"
                                    ],
                                    "format": "date-time"
                                },
                                "purchase_price": {"type": "number"},
                                "current_price": {"type": "number"},
                                "current_returns": {"type": "number"},
                                "trade_state": {
                                    "type": "string",
                                    "enum": ["UNFILLED", "FILLED"]
                                },
                                "order_id": {
                                    "type": [
                                        "string",
                                        "null"
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            "securities_set": {
                "type": "array",
                "minItems": 0,
                "items": {
                    "type": "object",
                    "required": [
                        "ticker_symbol", "analysis_price", "current_price", "current_returns"
                    ],
                    "properties": {
                        "ticker_symbol": {"type": "string"},
                        "analysis_price": {"type": "number"},
                        "current_price": {"type": "number"},
                        "current_returns": {"type": "number"}
                    }
                }
            }
        }
    }

    model_s3_folder_prefix = constants.S3_PORTFOLIO_FOLDER_PREFIX

    model_name = "Portfolio"

    def __init__(self, model_dict: dict):
        super().__init__(model_dict)

    def is_empty(self):
        '''
            Returns true of the portfolio is empty.
        '''
        try:
            return not len(self.model['current_portfolio']['securities']) > 0
        except Exception:
            return True

    def create_empty_portfolio(self, recommendation_set: object):
        '''
            Creates a new and empty portfolio object based on a recommendation set.
            Once created, the portfolio will be ready to trade

        '''
        securities = recommendation_set.to_dict()['securities_set']
        securities_list = []

        for security in securities:
            ticker = security['ticker_symbol']
            analysis_price = security['price']

            (price_date_str, latest_price) = intrinio_data.get_latest_close_price(
                ticker, datetime.now(), 5)
            securities_list.append(
                {
                    "ticker_symbol": ticker,
                    "analysis_price": analysis_price,
                    "current_price": latest_price,
                    "current_returns": ((latest_price / analysis_price) - 1),
                }
            )

        try:
            price_date = parser.parse(price_date_str).date()
        except Exception as e:
            raise ValidationError(
                "Could parse price date returned by Intrinio API", e)

        securities_set = {
            "securities_set": securities_list
        }

        self.model = {
            "portfolio_id": str(uuid.uuid1()),
            "set_id": recommendation_set.to_dict()['set_id'],
            "creation_date": util.datetime_to_iso_utc_string(datetime.now()),
            "price_date": str(price_date),
            "securities_set": securities_list
        }

        self.validate_model()

        log.info("Created empty portfolio using price date of: %s",
                 str(price_date))

    def reprice(self, price_date: datetime):
        '''
            Reads the current prices, computes the latest returns
            and updates the portfolio object.
        '''

        # Update the current returns in the securities set
        for security in self.model['securities_set']:
            analysis_price = security['analysis_price']
            (price_date_str, latest_price) = intrinio_data.get_latest_close_price(
                security['ticker_symbol'], price_date, 5)
            security['current_price'] = latest_price

        # if a portfolio exsts, reprice it too
        if not self.is_empty():
            for security in self.model['current_portfolio']['securities']:
                purchase_price = security['purchase_price']
                (price_date_str, latest_price) = intrinio_data.get_latest_close_price(
                    security['ticker_symbol'], price_date, 5)
                security['current_price'] = latest_price

        self.recalc_returns()

        # finally set the price date
        try:
            price_date = parser.parse(price_date_str).date()
        except Exception as e:
            raise ValidationError(
                "Could parse price date returned by Intrinio API", e)

        self.model['price_date'] = str(price_date)
        log.info("Repriced portfolio for date of %s" % str(price_date))

    def recalc_returns(self):
        '''
            Iterates through the portfolio and recalculates the retuns
        '''

        # Update the current returns in the securities set
        for security in self.model['securities_set']:
            analysis_price = security['analysis_price']
            latest_price = security['current_price']

            if analysis_price > 0:
                security['current_returns'] = (
                    (latest_price / analysis_price) - 1)
            else:
                security['current_returns'] = 0

        # if a portfolio exsts, reprice it too
        if not self.is_empty():
            for security in self.model['current_portfolio']['securities']:
                purchase_price = security['purchase_price']
                latest_price = security['current_price']

                if purchase_price > 0:
                    security['current_returns'] = (
                        (latest_price / purchase_price) - 1)
                else:
                    security['current_returns'] = 0

    def get_position(self, ticker: str):
        '''
            Returns the dictionary object for the given ticker, or None if
            not present in the portfolio
        '''
        for sec in self.model['current_portfolio']['securities']:
            if sec['ticker_symbol'] == ticker:
                return sec

        return None

    def copy(self):
        '''
            returns a copy of the portfolio
        '''
        return deepcopy(self)
