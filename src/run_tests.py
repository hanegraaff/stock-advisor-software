import unittest
import logging
from test.test_dataprovider_intrinio_util import TestDataProviderIntrinioUtil
from test.test_exceptions import TestExceptions
from test.test_dataprovider_intrinio_data import TestDataProviderIntrinioData
from test.test_support_financial_cache import TestFinancialCache

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] - %(message)s')


if __name__ == '__main__':
    unittest.main()