"""Author: Mark Hanegraaff -- 2020
    Testing class for the connectors.td_ameritrade module
"""
import unittest
import botocore
import os
import requests
import datetime
from copy import deepcopy
from unittest.mock import patch
from connectors import td_ameritrade
from exception.exceptions import ValidationError, TradeError
from support import constants


class TestConnectorsTDAmeritrade(unittest.TestCase):
    """
        Testing class for the connectors.td_ameritrade module
    """

    def test_generate_tags(self):
        tag = td_ameritrade.generate_tag()

        self.assertEqual(len(tag), 2)

    def test_get_credentials_not_set(self):
        with patch.object(os.environ, 'get',
                          side_effect=Exception("Not Found")):

            with self.assertRaises(ValidationError):
                td_ameritrade.get_credentials()

            self.assertEqual(len(td_ameritrade.missing_variables), 3)

    def test_get_credentials_valid(self):
        with patch.object(os.environ, 'get', return_value="X"):
            ret = td_ameritrade.get_credentials()

            self.assertTupleEqual(ret, ("X", "X", "X"))

    def test_request_with_exception(self):
        with patch.object(requests, 'request',
                          side_effect=requests.ConnectionError("Connection Error")):

            with self.assertRaises(TradeError):
                td_ameritrade.request('GET', "http://nowhere.com", None, None)

    def test_login_with_api_exception(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
            patch.object(requests, 'post',
                         side_effect=requests.ConnectionError("Connection Error")):

            with self.assertRaises(TradeError):
                td_ameritrade.login()

    '''
        equity market open tests
    '''

    # this would be typical response for a weekend of holiday
    def test_equity_market_open_holiday_weekend(self):
        '''
            Note that if this API is called on a holiday or weekend,
            the response will be different and needs to be handled appropriately
        '''
        td_equity_market_response = {
            "equity": {
                "equity": {
                    "date": "2020-05-10",
                    "marketType": "EQUITY",
                    "exchange": None,
                    "category": None,
                    "product": "equity",
                    "productName": None,
                    "isOpen": False,
                    "sessionHours": None
                }
            }
        }
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, td_equity_market_response)):

            time_now_utc = datetime.datetime(2020, 5, 10, 15, 0, 0)
            self.assertFalse(td_ameritrade.equity_market_open(time_now_utc))

    def test_equity_market_open_valid_response(self):
        '''
            When this API is called during a valid business date, the response
            will look like this.
        '''
        td_equity_market_response = {
            "equity": {
                "EQ": {
                    "date": "2020-05-05",
                    "marketType": "EQUITY",
                    "exchange": "NULL",
                    "category": "NULL",
                    "product": "EQ",
                    "productName": "equity",
                    "isOpen": True,
                    "sessionHours": {
                        "preMarket": [
                            {
                                "start": "2020-05-05T07:00:00-04:00",
                                "end": "2020-05-05T09:30:00-04:00"
                            }
                        ],
                        "regularMarket": [
                            {
                                "start": "2020-05-05T09:30:00-04:00",
                                "end": "2020-05-05T16:00:00-04:00"
                            }
                        ],
                        "postMarket": [
                            {
                                "start": "2020-05-05T16:00:00-04:00",
                                "end": "2020-05-05T20:00:00-04:00"
                            }
                        ]
                    }
                }
            }
        }

        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, td_equity_market_response)):

            time_now_utc = datetime.datetime(2020, 5, 5, 15, 0, 0)
            self.assertTrue(td_ameritrade.equity_market_open(time_now_utc))

            time_now_utc = datetime.datetime(2020, 5, 5, 0, 0, 0)
            self.assertFalse(td_ameritrade.equity_market_open(time_now_utc))

    '''
        Summarize Positions Tests
    '''

    td_account_response = {
        "securitiesAccount": {
            "type": "CASH",
            "accountId": "123456789",
            "roundTrips": 0,
            "isDayTrader": False,
            "isClosingOnlyRestricted": False,
            "positions": [
                {
                    "shortQuantity": 0.0,
                    "averagePrice": 1.0,
                    "currentDayProfitLoss": 0.0,
                    "currentDayProfitLossPercentage": 0.0,
                    "longQuantity": 100,
                    "settledLongQuantity": 100,
                    "settledShortQuantity": 0.0,
                    "instrument": {
                        "assetType": "CASH_EQUIVALENT",
                        "cusip": "9ZZZFD104",
                        "symbol": "MMDA1",
                        "description": "FDIC INSURED DEPOSIT ACCOUNT  CORE  NOT COVERED BY SIPC",
                        "type": "MONEY_MARKET_FUND"
                    },
                    "marketValue": 100,
                    "maintenanceRequirement": 0.0
                },
                {
                    "shortQuantity": 0.0,
                    "averagePrice": 100,
                    "currentDayProfitLoss": 0.0,
                    "currentDayProfitLossPercentage": 0.0,
                    "longQuantity": 1.0,
                    "settledLongQuantity": 1.0,
                    "settledShortQuantity": 0.0,
                    "instrument": {
                        "assetType": "EQUITY",
                        "cusip": "78463V107",
                        "symbol": "SPY"
                    },
                    "marketValue": 100,
                    "maintenanceRequirement": 0.0
                }
            ],
            "initialBalances": {
                "accruedInterest": 0.0,
                "cashAvailableForTrading": 1000,
                "cashAvailableForWithdrawal": 1000,
                "cashBalance": 0.0,
                "bondValue": 0.0,
                "cashReceipts": 0.0,
                "liquidationValue": 1100.00,
                "longOptionMarketValue": 0.0,
                "longStockValue": 1000.00,
                "moneyMarketFund": 100,
                "mutualFundValue": 0.0,
                "shortOptionMarketValue": 0.0,
                "shortStockValue": 0.0,
                "isInCall": False,
                "unsettledCash": 0.0,
                "cashDebitCallValue": 0.0,
                "pendingDeposits": 0.0,
                "accountValue": 1393.38
            },
            "currentBalances": {
                "accruedInterest": 0.0,
                "cashBalance": 0.0,
                "cashReceipts": 0.0,
                "longOptionMarketValue": 0.0,
                "liquidationValue": 1100.00,
                "longMarketValue": 1000.00,
                "moneyMarketFund": 100.00,
                "savings": 0.0,
                "shortMarketValue": 0.0,
                "pendingDeposits": 0.0,
                "cashAvailableForTrading": 1000.00,
                "cashAvailableForWithdrawal": 100.00,
                "cashCall": 0.0,
                "longNonMarginableMarketValue": 100.00,
                "totalCash": 0.0,
                "shortOptionMarketValue": 0.0,
                "mutualFundValue": 0.0,
                "bondValue": 0.0,
                "cashDebitCallValue": 0.0,
                "unsettledCash": 0.0
            },
            "projectedBalances": {
                "cashAvailableForTrading": 100.00,
                "cashAvailableForWithdrawal": 100.00
            }
        }
    }

    def test_positions_summary_valid_response(self):
        response = deepcopy(self.td_account_response)

        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, response)):

            summary = td_ameritrade.positions_summary()

            self.assertDictEqual(summary, {
                'cash': {'cashAvailableForTrading': 1000.0},
                'equities': {'SPY': {'averagePrice': 100,
                                     'longQuantity': 1.0,
                                     'marketValue': 100}
                             }
            })

    def test_positions_summary_no_positions(self):
        '''
            Tests that when positions are missing from the response, no
            exceptions are thrown
        '''
        response = deepcopy(self.td_account_response)
        del response['securitiesAccount']['positions']

        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, response)):

            summary = td_ameritrade.positions_summary()

            self.assertDictEqual(summary, {
                'cash': {'cashAvailableForTrading': 1000.0},
                'equities': {}
            })

    def test_positions_summary_not_cash_account(self):
        response = deepcopy(self.td_account_response)
        response['securitiesAccount']['type'] = 'MARGIN'

        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, response)):

            with self.assertRaises(ValidationError):
                td_ameritrade.positions_summary()

    '''
        Place order test
    '''

    def test_place_order_with_api_exception(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None), \
                patch.object(td_ameritrade, 'request', side_effect=TradeError("Some Error", None, None)):

            with self.assertRaises(TradeError):
                td_ameritrade.place_order("SELL", "xxx", 1, "SHARES")

    def test_place_order_with_valid_headers(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None), \
                patch.object(td_ameritrade, 'request', return_value=({
                    'Location': 'https://api.tdameritrade.com/v1/accounts/123456789/orders/0987654321'
                }, None)):

            order_id = td_ameritrade.place_order("SELL", "xxx", 1, "SHARES")
            self.assertEqual(order_id, '0987654321')

    def test_place_order_with_invalid_headers(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None), \
                patch.object(td_ameritrade, 'request', return_value=({}, None)):

            order_id = td_ameritrade.place_order("SELL", "xxx", 1, "SHARES")
            self.assertEqual(len(order_id), 2)

    def test_place_order_with_invalid_param_values(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None), \
                patch.object(td_ameritrade, 'request', return_value=({}, None)):

            with self.assertRaises(ValidationError):
                td_ameritrade.place_order("Something Else", "xxx", 1, "SHARES")

            with self.assertRaises(ValidationError):
                td_ameritrade.place_order("SELL", "xxx", 1, "NOT_VALID")

    '''
        List orders tests
    '''

    td_order_list = [{
        "session": "NORMAL",
        "duration": "DAY",
        "orderType": "MARKET",
        "complexOrderStrategyType": "NONE",
        "quantity": 1.0,
        "filledQuantity": 0.0,
        "remainingQuantity": 0.0,
        "requestedDestination": "AUTO",
        "destinationLinkName": "AutoRoute",
        "orderLegCollection": [
            {
                "orderLegType": "EQUITY",
                "legId": 1,
                "instrument": {
                    "assetType": "EQUITY",
                    "cusip": "111111111",
                    "symbol": "SPY"
                },
                "instruction": "SELL",
                "positionEffect": "CLOSING",
                "quantity": 1.0
            }
        ],
        "orderStrategyType": "SINGLE",
        "orderId": 2222222222,
        "cancelable": False,
        "editable": False,
        "status": "CANCELED",
        "enteredTime": "2020-05-05T02:54:07+0000",
        "closeTime": "2020-05-05T03:11:00+0000",
        "tag": "AA_User:a3",
        "accountId": 999999999
    },
        {
        "session": "NORMAL",
        "duration": "DAY",
        "orderType": "MARKET",
        "complexOrderStrategyType": "NONE",
        "quantity": 1.0,
        "filledQuantity": 0.0,
        "remainingQuantity": 0.0,
        "requestedDestination": "AUTO",
        "destinationLinkName": "AutoRoute",
        "orderLegCollection": [
            {
                "orderLegType": "EQUITY",
                "legId": 1,
                "instrument": {
                    "assetType": "EQUITY",
                    "cusip": "111111111",
                    "symbol": "SPY"
                },
                "instruction": "SELL",
                "positionEffect": "CLOSING",
                "quantity": 1.0
            }
        ],
        "orderStrategyType": "SINGLE",
        "orderId": 3333333333,
        "cancelable": False,
        "editable": False,
        "status": "CANCELED",
        "enteredTime": "2020-05-05T02:37:19+0000",
        "closeTime": "2020-05-05T02:37:36+0000",
        "tag": "AA_User:CR",
        "accountId": 999999999
    }]

    def test_list_recent_orders_valid_response(self):
        response = deepcopy(self.td_order_list)

        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, response)):

            order_summary = td_ameritrade.list_recent_orders()

            self.assertDictEqual(order_summary, {
                "2222222222": {
                    "status": "CANCELED",
                    "symbol": "SPY",
                    "quantity": 1.0,
                    "closeTime": "2020-05-05T03:11:00+0000",
                    "tag": "AA_User:a3",
                    "cancelable": False
                },
                "3333333333": {
                    "status": "CANCELED",
                    "symbol": "SPY",
                    "quantity": 1.0,
                    "closeTime": "2020-05-05T02:37:36+0000",
                    "tag": "AA_User:CR",
                    "cancelable": False,
                }
            })

    def test_list_recent_orders_no_orders(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None),\
                patch.object(td_ameritrade, 'request', return_value=(None, [])):

            order_summary = td_ameritrade.list_recent_orders()

            self.assertDictEqual(order_summary, {})

    def test_get_latest_equity_price_with_api_exception(self):
        with patch.object(td_ameritrade, 'get_credentials',
                          return_value=("aaa", "bbb", "ccc")), \
                patch.object(td_ameritrade, 'login', return_value=None), \
                patch.object(td_ameritrade, 'request', side_effect=TradeError("Some Error", None, None)):

            with self.assertRaises(TradeError):
                td_ameritrade.get_latest_equity_price("SPY")
