import unittest
import logging
from test.test_dataprovider_intrinio_util import TestDataProviderIntrinioUtil
from test.test_exceptions import TestExceptions
from test.test_dataprovider_intrinio_data import TestDataProviderIntrinioData
from test.test_support_financial_cache import TestFinancialCache
from test.test_strategies_price_dispersion import TestStrategiesPriceDispersion
from test.test_strategies_portfolio import TestStrategiesPortfolio


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')


if __name__ == '__main__':
    unittest.main()