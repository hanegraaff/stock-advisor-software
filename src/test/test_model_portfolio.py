"""Author: Mark Hanegraaff -- 2020
    Testing class for the model.portfolio module
"""
import unittest
from unittest.mock import patch
import dateutil.parser as parser
from datetime import datetime
from exception.exceptions import ValidationError, DataError
from model.portfolio import Portfolio
from model.recommendation_set import SecurityRecommendationSet
from connectors import intrinio_data
from support import util


class TestPortfolio(unittest.TestCase):
    """
        Testing class for the model.portfolio module
    """

    def test_valid_object(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": {
                "securities": [{
                    "ticker_symbol": "AAPL",
                    "quantity": 1000,
                    "purchase_date": "2020-03-31T04:00:00+00:00",
                    "purchase_price": 123.45,
                    "current_price": 234.56,
                    "current_returns": 0.9,
                    "trade_state": "FILLED",
                    "order_id": None
                }]
            },
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 100,
                "current_price": 102,
                "current_returns": 0.02
            }]
        }

        Portfolio.from_dict(portfolio_dict)

    def test_valid_object_no_portfolio(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": {
                "securities": [{
                    "ticker_symbol": "AAPL",
                    "quantity": 1000,
                    "purchase_date": "2020-03-31T04:00:00+00:00",
                    "purchase_price": 123.45,
                    "current_price": 234.56,
                    "current_returns": 0.9,
                    "trade_state": "FILLED",
                    "order_id": None
                }]
            },
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 100,
                "current_price": 102,
                "current_returns": 0.02
            }]
        }

        Portfolio.from_dict(portfolio_dict)

    def test_invalid_object_no_securities_set(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "current_portfolio": {
                "price_date": "2020-03-31T04:00:00+00:00",
                "securities": [{
                    "ticker_symbol": "AAPL",
                    "quantity": 1000,
                    "purchase_date": "2020-03-31T04:00:00+00:00",
                    "purchase_price": 123.45,
                    "current_price": 234.56,
                    "current_returns": 0.9,
                    "trade_state": "FILLED",
                    "order_id": None
                }]
            }
        }

        with self.assertRaises(ValidationError):
            Portfolio.from_dict(portfolio_dict)

    def test_invalid_object_missing_properties(self):
        portfolio_dict = {
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": [{
                "ticker_symbol": "AAPL",
                "quantity": 1000,
                "purchase_date": "2020-03-31T04:00:00+00:00",
                "purchase_price": 123.45,
                "current_price": 234.56,
                "current_returns": 0.9,
                "trade_state": "FILLED",
                "order_id": None
            }],
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 100,
                "current_price": 102,
                "current_returns": 0.02
            }]
        }

        with self.assertRaises(ValidationError):
            Portfolio.from_dict(portfolio_dict)

    '''
        Create a security recommendation dictionary and use it from
        the next few tests
    '''
    sr_dict = {
        "set_id": "1430b59a-5b79-11ea-8e96-acbc329ef75f",
        "creation_date": "2020-09-01T04:56:57.612693+00:00",
        "valid_from": "2019-08-01T04:00:00+00:00",
        "valid_to": "2019-08-31T04:00:00+00:00",
        "price_date": "2019-09-01T02:34:12.876012+00:00",
        "strategy_name": "PRICE_DISPERSION",
        "security_type": "US Equities",
        "securities_set": [{
            "ticker_symbol": "GE",
            "price": 102,
        }, {
            "ticker_symbol": "INTC",
            "analysis_price": 100,
            "price": 102
        }, {
            "ticker_symbol": "AAPL",
            "analysis_price": 100,
            "price": 102
        }]
    }

    def test_create_empty_portfolio_no_prices(self):
        with patch.object(intrinio_data, 'get_latest_close_price',
                          side_effect=DataError("test exception", None)):

            recommendation_set = SecurityRecommendationSet.from_dict(
                self.sr_dict)

            with self.assertRaises(DataError):
                portfolio = Portfolio()
                portfolio.create_empty_portfolio(recommendation_set)

    def test_create_empty_portfolio_invalid_intrinio_response(self):
        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('aaaa', 123.45)):

            recommendation_set = SecurityRecommendationSet.from_dict(
                self.sr_dict)

            with self.assertRaises(ValidationError):
                portfolio = Portfolio()
                portfolio.create_empty_portfolio(recommendation_set)

    def test_create_empty_portfolio_valid(self):
        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('2019-08-31', 123.45)):

            recommendation_set = SecurityRecommendationSet.from_dict(
                self.sr_dict)

            portfolio = Portfolio()
            portfolio.create_empty_portfolio(recommendation_set)

    def test_portfolio_empty(self):
        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('2019-08-31', 123.45)):

            recommendation_set = SecurityRecommendationSet.from_dict(
                self.sr_dict)

            portfolio = Portfolio()
            portfolio.create_empty_portfolio(recommendation_set)

            self.assertTrue(portfolio.is_empty())

    def test_portfolio_not_empty(self):
        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('2019-08-31', 123.45)):

            recommendation_set = SecurityRecommendationSet.from_dict(
                self.sr_dict)

            portfolio = Portfolio()
            portfolio.create_empty_portfolio(recommendation_set)

            portfolio.model['current_portfolio'] = {
                'securities': [{
                    "ticker_symbol": "ABC",
                    "purchase_date": "2019-09-01T02:34:12.876012+00:00",
                    "purchase_price": 100,
                    "current_price": 200,
                    "trade_state": "FILLED",
                    "order_id": None
                }]
            }

            self.assertFalse(portfolio.is_empty())

    def test_reprice_filled_order(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": {
                "securities": [{
                    "ticker_symbol": "INTC",
                    "quantity": 100,
                    "purchase_date": "2020-03-31T04:00:00+00:00",
                    "purchase_price": 100,
                    "current_price": 100,
                    "current_returns": 0,
                    "trade_state": "FILLED",
                    "order_id": None
                }]
            },
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 100,
                "current_price": 100,
                "current_returns": 0
            }]
        }

        portfolio = Portfolio.from_dict(portfolio_dict)

        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('2020-04-30', 101)):

            now = datetime.now()

            portfolio.reprice(now)

            self.assertEqual(portfolio.model["current_portfolio"][
                             "securities"][0]["current_price"], 101)
            self.assertEqual(round(portfolio.model["current_portfolio"][
                             "securities"][0]["current_returns"], 2), 0.01)

            self.assertEqual(portfolio.model["securities_set"]
                             [0]["current_price"], 101)
            self.assertEqual(round(portfolio.model["securities_set"][
                             0]["current_returns"], 2), 0.01)

            self.assertEqual(portfolio.model["price_date"], util.date_to_iso_utc_string(
                parser.parse('2020-04-30')))

    def test_reprice_unfilled_order(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": {
                "securities": [{
                    "ticker_symbol": "INTC",
                    "quantity": 100,
                    "purchase_date": "2020-03-31T04:00:00+00:00",
                    "purchase_price": 0,
                    "current_price": 0,
                    "current_returns": 0,
                    "trade_state": "UNFILLED",
                    "order_id": None
                }]
            },
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 0,
                "current_price": 0,
                "current_returns": 0
            }]
        }

        portfolio = Portfolio.from_dict(portfolio_dict)

        with patch.object(intrinio_data, 'get_latest_close_price',
                          return_value=('2020-04-30', 101)):

            now = datetime.now()

            portfolio.reprice(now)

            self.assertEqual(portfolio.model["current_portfolio"][
                             "securities"][0]["current_price"], 101)
            self.assertEqual(round(portfolio.model["current_portfolio"][
                             "securities"][0]["current_returns"], 2), 0)

            self.assertEqual(portfolio.model["securities_set"]
                             [0]["current_price"], 101)
            self.assertEqual(round(portfolio.model["securities_set"][
                             0]["current_returns"], 2), 0)

            self.assertEqual(portfolio.model["price_date"], util.date_to_iso_utc_string(
                parser.parse('2020-04-30')))

    def test_get_position(self):
        portfolio_dict = {
            "portfolio_id": "xxx",
            "set_id": "yyy",
            "creation_date": "2020-04-14T12:20:50.219487+00:00",
            "price_date": "2020-03-31T04:00:00+00:00",
            "current_portfolio": {
                "securities": [{
                    "ticker_symbol": "INTC",
                    "quantity": 100,
                    "purchase_date": None,
                    "purchase_price": 100,
                    "current_price": 100,
                    "current_returns": 0,
                    "trade_state": "UNFILLED",
                    "order_id": None
                }]
            },
            "securities_set": [{
                "ticker_symbol": "AAPL",
                "analysis_price": 100,
                "current_price": 100,
                "current_returns": 0
            }]
        }

        portfolio = Portfolio.from_dict(portfolio_dict)

        self.assertIsNotNone(portfolio.get_position("INTC"))
        self.assertIsNone(portfolio.get_position("XXX"))
