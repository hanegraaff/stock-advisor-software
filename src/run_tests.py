"""Author: Mark Hanegraaff -- 2020

Pytest driver. All unit tests are run from this script.
"""
import unittest
import logging
from test.test_exceptions import TestExceptions
from test.test_support_financial_cache import TestFinancialCache
from test.test_support_configuration import TestConfiguration
from test.test_support_util import TestSupportUtil
from test.test_strategies_price_dispersion import TestStrategiesPriceDispersion
from test.test_strategies_macd_crossover import TestStrategiesMACDCrossover
from test.test_strategies_calculator import TestStrategiesCalculator
from test.test_connectors_aws_service_wrapper import TestConnectorsAWSServiceWrapper
from test.test_connectors_td_ameritrade import TestConnectorsTDAmeritrade
from test.test_connectors_intrinio_util import TestConnectorsIntrinioUtil
from test.test_connectors_intrinio_data import TestConnectorsIntrinioData
from test.test_connector_connector_test import TestConnectorsTest
from test.test_services_recommendation import TestServicesRecommendation
from test.test_services_portfolio_mgr import TestServicePortfolioManager
from test.test_services_broker import TestBroker
from test.test_model_ticker_list import TestModelTickerList
from test.test_model_recommendation_set import TestSecurityRecommendationSet
from test.test_model_base_model import TestBaseModel
from test.test_model_portfolio import TestPortfolio

logging.basicConfig(level=logging.ERROR,
                    format='[%(levelname)s] - %(message)s')

if __name__ == '__main__':
    unittest.main()
