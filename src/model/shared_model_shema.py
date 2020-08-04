"""Author: Mark Hanegraaff -- 2020

This module contains shared schema objects shared between models

"""

SHARED_MODEL_SCHEMA = {
  "definitions": {
    "order":{
        "type": "object",
        "required": [
            "price", "date", "order_id", "order_status", "reason"
        ],
        "properties": {
            "price": {"type": "number"},
            "date": {
                "type": ["string", "null"],
                "format": "date-time"
            },
            "order_id": {"type": ["string", "null"]},
            "order_status": {
                "type": "string",
                "enum": ["UNFILLED", "FILLED"]
            },
            "reason": {"type": "string"}
        },
        "additionalProperties": False
    },
    "position": {
        "type": "object",
        "required": [
            "ticker_symbol", "ls_indicator", "strategy_name", "current_price",
            "quantity", "pnl"
        ],
        "properties": {
            "ticker_symbol": {"type": "string"},
            "ls_indicator":{
                "type": "string",
                "enum": ["LONG", "SHORT"]
            },
            "pending_command": {
                "type": "object",
                "required": [
                    "action", "reason"
                ],
                "properties":{
                    "action": {"type": "string"},
                    "reason": {"type": "string"}
                }
            },
            "strategy_name": {"type": "string"},
            "current_price": {"type": "number"},
            "quantity": {"type": "number"},
            "pnl": {"type": "number"},
            "open":{ "$ref": "#/definitions/order"},
            "close":{ "$ref": "#/definitions/order"}
        },
        "additionalProperties": False
    }
  }
}