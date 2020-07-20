"""Author: Mark Hanegraaff -- 2020

This module contains shared schema objects shared between models

"""

SHARED_MODEL_SCHEMA = {
  "definitions": {
    "order":{
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
    "position": {
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
            "open":{ "$ref": "#/definitions/order"},
            "close":{ "$ref": "#/definitions/order"}
        }
    }
  }
}