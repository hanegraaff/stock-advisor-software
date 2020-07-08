"""Author: Mark Hanegraaff -- 2020
    Testing class for the services.portfolio_mgr_svc module
"""
import unittest
from unittest.mock import patch, Mock
from copy import deepcopy
from datetime import datetime
from exception.exceptions import ValidationError, AWSError
from services import portfolio_mgr_svc
from support import constants
from model.recommendation_set import SecurityRecommendationSet
from model.portfolio import Portfolio
from connectors import aws_service_wrapper


class TestServicePortfolioManager(unittest.TestCase):

    """Author: Mark Hanegraaff -- 2020
        Testing class for the services.portfolio_mgr_svc module
    """

    '''
        validate_environment tests
    '''

    def test_get_service_inputs_with_s3_exception(self):
        with patch.object(SecurityRecommendationSet, 'from_s3',
                          side_effect=AWSError("test error", None)):

            with self.assertRaises(AWSError):
                portfolio_mgr_svc.get_service_inputs('sa')

    def test_get_service_inputs_not_current(self):
        with patch.object(SecurityRecommendationSet, 'from_s3',
                          return_value=SecurityRecommendationSet), \
            patch.object(SecurityRecommendationSet, 'is_current',
                         return_value=False):

            with self.assertRaises(ValidationError):
                portfolio_mgr_svc.get_service_inputs('sa')

    def test_get_service_inputs_portfolio_not_found(self):
        with patch.object(SecurityRecommendationSet, 'from_s3',
                          return_value=SecurityRecommendationSet), \
            patch.object(SecurityRecommendationSet, 'is_current',
                         return_value=True), \
            patch.object(Portfolio, 'from_s3',
                         side_effect=AWSError("", Exception("(404) Not found"))):
            portfolio = portfolio_mgr_svc.get_service_inputs('sa')[0]
            self.assertEqual(portfolio, None)

    def test_get_service_inputs_portfolio_error(self):
        with patch.object(SecurityRecommendationSet, 'from_s3',
                          return_value=SecurityRecommendationSet), \
            patch.object(SecurityRecommendationSet, 'is_current',
                         return_value=True), \
            patch.object(Portfolio, 'from_s3',
                         side_effect=AWSError("", None)):

            with self.assertRaises(AWSError):
                portfolio_mgr_svc.get_service_inputs('sa')

    '''
        update_portfolio tests
    '''

    portfolio_dict = {
        "portfolio_id": "xxx",
        "set_id": "yyy",
        "creation_date": "2020-04-14T12:20:50.219487+00:00",
        "price_date": "2020-03-31",
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

    sr_dict = {
        "set_id": "yyyy",
        "creation_date": "2020-09-01T04:56:57.612693+00:00",
        "valid_from": "2019-08-01",
        "valid_to": "2019-09-01",
        "price_date": "2019-08-30",
        "strategy_name": "PRICE_DISPERSION",
        "security_type": "US Equities",
        "securities_set": [{
            "ticker_symbol": "GE",
            "price": 123.45
        }, {
            "ticker_symbol": "INTC",
            "price": 123.45
        }, {
            "ticker_symbol": "AAPL",
            "price": 123.45
        }]
    }

    def test_update_portfolio_too_small(self):
        security_recommendation = SecurityRecommendationSet.from_dict(
            self.sr_dict)
        portfolio = Portfolio(None)
        portfolio.create_empty_portfolio(security_recommendation)

        with self.assertRaises(ValidationError):
            portfolio_mgr_svc.update_portfolio(
                portfolio, security_recommendation, 0)

    def test_update_portfolio_too_big(self):
        security_recommendation = SecurityRecommendationSet.from_dict(
            self.sr_dict)
        portfolio = Portfolio(None)
        portfolio.create_empty_portfolio(security_recommendation)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(
            portfolio, security_recommendation, 100)

        '''
            ensure that portfolio contains all securitie from the recommendation set
        '''

        self.assertTrue(updated)
        self.assertEqual(len(new_p.model['current_portfolio'][
                         'securities']), len(security_recommendation.model['securities_set']))
        self.assertEqual(len(new_p.model['securities_set']), 0)

    def test_update_portfolio_empty_portfolio(self):
        security_recommendation = SecurityRecommendationSet.from_dict(
            self.sr_dict)
        portfolio = Portfolio(None)
        portfolio.create_empty_portfolio(security_recommendation)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(
            portfolio, security_recommendation, 1)

        '''
            ensure that
            1) portfolio is updated
            2) portfolio contains 1 security
            3) portfolio contains nothing in the security set
        '''

        self.assertTrue(updated)
        self.assertEqual(
            len(new_p.model['current_portfolio']['securities']), 1)
        self.assertEqual(len(new_p.model['securities_set']), len(
            security_recommendation.model['securities_set']) - 1)

    def test_update_portfolio_new_recommendation(self):

        sr_mod = deepcopy(self.sr_dict)
        sr_mod['set_id'] = 'different_set'

        security_recommendation = SecurityRecommendationSet.from_dict(sr_mod)
        portfolio = Portfolio.from_dict(self.portfolio_dict)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(
            portfolio, security_recommendation, 1)

        '''
            ensure that
            1) portfolio is updated
            2) set id are being set properly
        '''

        self.assertTrue(updated)
        self.assertEqual(new_p.model['set_id'],
                         security_recommendation.model['set_id'])
        self.assertNotEqual(new_p.model['set_id'], self.sr_dict['set_id'])

    def test_update_portfolio_nothing_new(self):
        sr_mod = deepcopy(self.sr_dict)
        p_mod = deepcopy(self.portfolio_dict)

        sr_mod['set_id'] = 'same_set'
        p_mod['set_id'] = 'same_set'

        security_recommendation = SecurityRecommendationSet.from_dict(sr_mod)
        portfolio = Portfolio.from_dict(p_mod)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(
            portfolio, security_recommendation, 1)

        '''
            ensure that
            1) portfolio is updated
            2) set id are being set properly
        '''

        self.assertFalse(updated)
        self.assertEqual(new_p.model['set_id'],
                         security_recommendation.model['set_id'])
        self.assertEqual(new_p.model['set_id'], p_mod['set_id'])

    '''
        Notification test
    '''

    def test_publish_current_returns(self):

        security_recommendation = SecurityRecommendationSet.from_dict(
            self.sr_dict)
        portfolio = Portfolio(None)
        portfolio.create_empty_portfolio(security_recommendation)
        (new_p, updated) = portfolio_mgr_svc.update_portfolio(
            portfolio, security_recommendation, 1)

        with patch.object(aws_service_wrapper, 'sns_publish_notification',
                          side_effect=AWSError("", None)), \
            patch.object(aws_service_wrapper, 'cf_read_export_value',
                         return_value="some_value"):

            with self.assertRaises(AWSError):
                portfolio_mgr_svc.publish_current_returns(new_p, updated, 'sa')
