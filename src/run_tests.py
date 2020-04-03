import unittest
import logging
from test.test_dataprovider_intrinio_util import TestDataProviderIntrinioUtil
from test.test_exceptions import TestExceptions
from test.test_dataprovider_intrinio_data import TestDataProviderIntrinioData
from test.test_support_financial_cache import TestFinancialCache
from test.test_strategies_price_dispersion import TestStrategiesPriceDispersion
from test.test_strategies_calculator import TestStrategiesCalculator
from test.test_cloud_aws_service_wrapper import TestCloudAWSServiceWrapper
from test.test_service_support_recommendation import TestServiceSupportRecommendation
from test.test_model_ticker_file import TestModelTickerFile
from test.test_model_recommendation_set import TestSecurityRecommendationSet

logging.basicConfig(level=logging.WARN, format='[%(levelname)s] - %(message)s')


if __name__ == '__main__':
    unittest.main()