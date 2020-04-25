import unittest
from unittest.mock import patch, Mock
from copy import deepcopy
from datetime import datetime
from exception.exceptions import ValidationError, AWSError
from service_support import portfolio_mgr_svc
from support import constants
from model.recommendation_set import SecurityRecommendationSet
from model.portfolio import Portfolio
from cloud import aws_service_wrapper

class TestServiceSupportPortfolioManager(unittest.TestCase):

    '''
        validate_environment tests
    '''

    def test_get_service_inputs_with_s3_exception(self):
        with patch.object(SecurityRecommendationSet, 'from_s3', \
            side_effect=AWSError("test error", None)):

            with self.assertRaises(AWSError):
                portfolio_mgr_svc.get_service_inputs('sa')

    def test_get_service_inputs_not_current(self):
        with patch.object(SecurityRecommendationSet, 'from_s3', \
            return_value=SecurityRecommendationSet), \
            patch.object(SecurityRecommendationSet, 'is_current', \
            return_value=False):

            with self.assertRaises(ValidationError):
                portfolio_mgr_svc.get_service_inputs('sa')

    def test_get_service_inputs_portfolio_not_found(self):
        with patch.object(SecurityRecommendationSet, 'from_s3', \
        return_value=SecurityRecommendationSet), \
        patch.object(SecurityRecommendationSet, 'is_current', \
        return_value=True), \
        patch.object(Portfolio, 'from_s3', \
        side_effect=AWSError("", Exception("(404) Not found"))):
            p = portfolio_mgr_svc.get_service_inputs('sa')[0]
            self.assertEqual(p, None)

    def test_get_service_inputs_portfolio_error(self):
        with patch.object(SecurityRecommendationSet, 'from_s3', \
            return_value=SecurityRecommendationSet), \
            patch.object(SecurityRecommendationSet, 'is_current', \
            return_value=True), \
            patch.object(Portfolio, 'from_s3', \
            side_effect=AWSError("", None)):

            with self.assertRaises(AWSError):
                portfolio_mgr_svc.get_service_inputs('sa')

            
    '''
        update_portfilio tests
    '''

    portfolio_dict = {
        "portfolio_id" : "xxx",
        "set_id" : "yyy",
        "creation_date" : "2020-04-14T12:20:50.219487+00:00",
        "price_date" : "2020-03-31T04:00:00+00:00",
        "current_portfolio": {
            "securities" : [{
                "ticker_symbol" : "INTC",
                "quantity" : 100,
                "purchase_date" : "2020-03-31T04:00:00+00:00",
                "purchase_price":  100,
                "current_price" : 100,
                "current_returns": 0
            }]
        },
        "securities_set":[{
            "ticker_symbol" : "AAPL",
            "analysis_price" : 100,
            "current_price" : 100,
            "current_returns": 0
        }]
    }

    sr_dict = {
        "set_id": "yyyy",
        "creation_date": "2020-09-01T04:56:57.612693+00:00",
        "analysis_start_date": "2019-08-01T04:00:00+00:00",
        "analysis_end_date": "2019-08-31T04:00:00+00:00",
        "price_date": "2019-09-01T02:34:12.876012+00:00",
        "strategy_name": "PRICE_DISPERSION",
        "security_type": "US Equities",
        "securities_set": [{
            "ticker_symbol" : "GE",
            "price": 123.45
        },{
            "ticker_symbol" : "INTC",
            "price": 123.45
        },{
            "ticker_symbol" : "AAPL",
            "price": 123.45
        }]
    }

    def test_update_portfolio_too_big(self):
        sr = SecurityRecommendationSet.from_dict(self.sr_dict)
        p = Portfolio()
        p.create_empty_portfolio(sr)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(p, sr, 100)

        '''
            ensure that portfolio contains all securitie from the recommendation set
        '''

        self.assertTrue(updated)
        self.assertEqual(len(new_p.model['current_portfolio']['securities']), len(sr.model['securities_set']))
        self.assertEqual(len(new_p.model['securities_set']), 0)


    def test_update_portfolio_empty_portfolio(self):
        sr = SecurityRecommendationSet.from_dict(self.sr_dict)
        p = Portfolio()
        p.create_empty_portfolio(sr)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(p, sr, 1)

        '''
            ensure that
            1) portfolio is updated
            2) portfolio contains 1 security
            3) portfolio contains nothing in the security set
        '''

        self.assertTrue(updated)
        self.assertEqual(len(new_p.model['current_portfolio']['securities']), 1)
        self.assertEqual(len(new_p.model['securities_set']), len(sr.model['securities_set']) - 1)


    def test_update_portfolio_new_recommendation(self):

        sr_mod = deepcopy(self.sr_dict)
        sr_mod['set_id'] = 'different_set'

        sr = SecurityRecommendationSet.from_dict(sr_mod)
        p = Portfolio()
        p.create_empty_portfolio(sr)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(p, sr, 1)

        '''
            ensure that
            1) portfolio is updated
            2) set id are being set properly
        '''

        self.assertTrue(updated)
        self.assertEqual(new_p.model['set_id'], sr.model['set_id'])
        self.assertNotEqual(new_p.model['set_id'], self.sr_dict['set_id'])

    def test_update_portfolio_nothing_new(self):
        sr_mod = deepcopy(self.sr_dict)
        p_mod = deepcopy(self.portfolio_dict)

        sr_mod['set_id'] = 'same_set'
        p_mod['set_id'] = 'same_set'

        sr = SecurityRecommendationSet.from_dict(sr_mod)
        p = Portfolio.from_dict(p_mod)

        (new_p, updated) = portfolio_mgr_svc.update_portfolio(p, sr, 1)

        '''
            ensure that
            1) portfolio is updated
            2) set id are being set properly
        '''

        self.assertFalse(updated)
        self.assertEqual(new_p.model['set_id'], sr.model['set_id'])
        self.assertEqual(new_p.model['set_id'], p_mod['set_id'])

    '''
        Notification test
    '''

    def test_publish_current_returns(self):

        sr = SecurityRecommendationSet.from_dict(self.sr_dict)
        p = Portfolio()
        p.create_empty_portfolio(sr)
        (new_p, updated) = portfolio_mgr_svc.update_portfolio(p, sr, 1)


        with patch.object(aws_service_wrapper, 'sns_publish_notification', \
            side_effect=AWSError("", None)):
            
            with self.assertRaises(AWSError):
                portfolio_mgr_svc.publish_current_returns(new_p, updated, 'sa')
    




